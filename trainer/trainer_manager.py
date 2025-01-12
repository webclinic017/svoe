from typing import Optional, Dict, Any, List, Type

from ray.serve.deployment import Deployment
import yaml
from pydantic import BaseModel
from ray.air import ScalingConfig, RunConfig, Checkpoint
from ray.air.integrations.mlflow import MLflowLoggerCallback
from ray.data import Dataset
from ray.train.base_trainer import BaseTrainer
from ray.train.batch_predictor import BatchPredictor
from ray.train.predictor import Predictor
from ray.train.xgboost import XGBoostTrainer, XGBoostPredictor
from ray.tune import TuneConfig, Tuner

from common.pandas.df_utils import plot_multi
from featurizer.runner import Featurizer
from trainer.svoe_mlflow_client import REMOTE_TRACKING_URI, LOCAL_TRACKING_URI, SvoeMLFlowClient

import ray
from ray.tune.search import sample


class XGBoostParams(BaseModel):
    num_boost_rounds: int
    train_valid_test_split: List[float]
    params: Dict[str, Any]


class TunerConfig(BaseModel):
    param_space: Dict
    num_samples: Optional[int] = 1
    metric: str
    mode: str
    max_concurrent_trials: Optional[int] = 1
    time_budget_s: Optional[int] = None
    search_alg: Optional[str] = None
    scheduler: Optional[str] = None


# TODO worker spec?
class TrainerConfig(BaseModel):
    xgboost: Optional[XGBoostParams]
    num_workers: int
    tuner_config: Optional[TunerConfig]

    @classmethod
    def load_config(cls, path: str) -> 'TrainerConfig':
        with open(path, 'r') as stream:
            d = yaml.safe_load(stream)
            return TrainerConfig.parse_obj(d)


# TODO rename to runner?
class TrainerManager:

    def __init__(self, config: TrainerConfig, ray_address: str):
        self.requires_tuner = TrainerManager._validate_config(config)
        self.trainer_config = config
        self.ray_address = ray_address
        pass

    @classmethod
    def _validate_config(cls, config: TrainerConfig) -> bool:
        required_params = ['xgboost', 'pytorch']
        config_args_keys = list(config.__dict__.keys())
        intersect = list(set(required_params).intersection(set(config_args_keys)))
        if len(intersect) != 1:
            raise ValueError(f'Tuner config should have exactly one of {required_params} fields')

        # TODO verify TunerConfig.max_concurrent_trials, TrainerConfig.num_workers (and worker_spec) play nicely together
        # TODO with cluster's available workers to avoid deadlock

        requires_tuner = config.tuner_config is not None
        return requires_tuner

    def _parse_param_space_config(self) -> Dict:
        # example
        # param_space = {
        #     'params': {
        #         'max_depth':
        #               'randint':
        #                   'lower': 2
        #                   'upper': 8,
        #         'min_child_weight':
        #               'randint':
        #                   'lower': 1
        #                   'upper': 10,
        #     },
        # },
        # TODO support sample_from?
        # from ray.tune.search.sample
        func_name_to_callable = {
            'randint': sample.randint,
            'uniform': sample.uniform,
            'quniform': sample.quniform,
            'loguniform': sample.loguniform,
            'qloguniform': sample.qloguniform,
            'choice': sample.choice,
            'lograndint': sample.lograndint,
            'qrandint': sample.qrandint,
            'qlograndint': sample.qlograndint,
            'randn': sample.randn,
            'qrandn': sample.qrandn,
        }

        param_space_raw = self.trainer_config.tuner_config.param_space
        params_raw = param_space_raw['params']
        params = {}
        for param_name in params_raw:
            func_name = list(params_raw[param_name].keys())[0]
            if func_name not in func_name_to_callable:
                raise ValueError(f'Unnknown function {func_name}')
            func = func_name_to_callable[func_name]
            kwargs = params_raw[param_name][func_name]
            params[param_name] = func(**kwargs)

        return {'params': params}

    def _build_run_config(self, trainer_run_id: str, tags: Dict) -> RunConfig:
        return RunConfig(
            verbose=2,
            callbacks=[MLflowLoggerCallback(
                tracking_uri=LOCAL_TRACKING_URI,
                experiment_name=trainer_run_id,
                tags=tags,
                save_artifact=True)]
        )

    def _build_trainer(self, run_config: RunConfig) -> BaseTrainer:
        if self.trainer_config.xgboost is not None:
            return self._build_xgboost_trainer(run_config=run_config)
        else:
            raise ValueError('Unknown trainer type')

    def _build_xgboost_trainer(self, run_config: RunConfig) -> XGBoostTrainer:
        feature_label_set = Featurizer.get_dataset()
        print(f'Starting trainer for dataset: {feature_label_set}')
        label_column = Featurizer.get_label_column(feature_label_set)

        train_valid_test_split = self.trainer_config.xgboost.train_valid_test_split
        train_ds, valid_ds, test_ds = feature_label_set.split_proportionately(train_valid_test_split)

        # TODO validate dataset has ['timestamp', 'receipt_timestamp'] cols
        xgboost_datasets = {
            'train': train_ds.drop_columns(cols=['timestamp', 'receipt_timestamp']),
            'valid': valid_ds.drop_columns(cols=['timestamp', 'receipt_timestamp'])
        }
        trainer = XGBoostTrainer(
            scaling_config=ScalingConfig(num_workers=self.trainer_config.num_workers, use_gpu=False),
            label_column=label_column,
            params=self.trainer_config.xgboost.params,
            # TODO set run name?
            run_config=run_config,
            # TODO re what valid is used for
            # https://www.kaggle.com/questions-and-answers/61835
            datasets=xgboost_datasets,
            # preprocessor=preprocessor, # XGBoost does not need feature scaling
            num_boost_round=self.trainer_config.xgboost.num_boost_rounds,
        )
        return trainer

    def _build_tuner(self, trainer: BaseTrainer, run_config: RunConfig) -> Tuner:
        return Tuner(
            trainer,
            run_config=run_config,
            param_space=self._parse_param_space_config(),
            tune_config=TuneConfig(
                num_samples=self.trainer_config.tuner_config.num_samples,
                metric=self.trainer_config.tuner_config.metric,
                mode=self.trainer_config.tuner_config.mode,
                max_concurrent_trials=self.trainer_config.tuner_config.max_concurrent_trials
            ),
        )

    def run(self, trainer_run_id: str, tags: Dict):
        with ray.init(address=self.ray_address, ignore_reinit_error=True, runtime_env={
            'pip': ['xgboost', 'xgboost_ray', 'mlflow']
        }):
            # TODO
            # INFO tuner_internal.py:90 -- A `RunConfig` was passed to both the `Tuner` and the `XGBoostTrainer`.
            # The run config passed to the `Tuner` is the one that will be used.
            run_config = self._build_run_config(trainer_run_id=trainer_run_id, tags=tags)
            trainer = self._build_trainer(run_config=run_config)
            if self.requires_tuner:
                tuner = self._build_tuner(trainer=trainer, run_config=run_config)
                tuner.fit()
            else:
                trainer.fit()

    # TODO sampling
    @classmethod
    def generate_predictions_dataset(cls, model_checkpoint: Checkpoint, predictor_class: Type[Predictor], num_workers: int) -> Dataset:
        feature_label_set = Featurizer.get_dataset()
        feature_columns = Featurizer.get_feature_columns(feature_label_set)
        label_column = Featurizer.get_label_column(feature_label_set)
        keep_columns = [label_column, 'timestamp']
        keep_columns.extend(feature_columns)
        batch_predictor = BatchPredictor.from_checkpoint(
            model_checkpoint, predictor_class
        )
        predicted_labels = batch_predictor.predict(
            data=feature_label_set,
            feature_columns=feature_columns,
            keep_columns=keep_columns,
            max_scoring_workers=num_workers,
            num_cpus_per_worker=1 # TODO pass more resource related args here
        )

        # TODO cache this to avoid recalculation
        return predicted_labels


if __name__ == '__main__':
    # tempdir, path = download_file('s3://svoe-remote-code/1/svoe_airflow.operators.svoe_python_operator.SvoePythonOperator/5e0d8a6714798ab5138596693e2ec6ab/test_remote_code_v1.py')
    # tempdir.cleanup()
    # print(path)
    # user_id = '1'
    conf_path = './trainer-config.yaml'
    config = TrainerConfig.load_config(conf_path)
    trainer_manager = TrainerManager(config=config, ray_address='ray://127.0.0.1:10001')
    trainer_manager.run(trainer_run_id='sample-run-id', tags={})

    # client = SvoeMLFlowClient()
    # best_model = client.get_best_checkpoint(metric_name='valid-logloss')
    # ds = TrainerManager.generate_predictions_dataset(best_model, XGBoostPredictor, 4)
    # df = ds.to_pandas()
    # print(df)
    # plot_multi(df)

