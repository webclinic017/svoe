from typing import Optional, Dict, List

import pandas as pd
import pyarrow

from common.pandas.df_utils import concat, downsample_uniform
from featurizer.actors.cache_actor import get_cache_actor, create_cache_actor
from featurizer.task_graph.builder import build_feature_label_set_task_graph
from featurizer.task_graph.executor import execute_graph
from featurizer.sql.db_actor import create_db_actor
from featurizer.storage.featurizer_storage import FeaturizerStorage
from featurizer.config import FeaturizerConfig
from featurizer.features.feature_tree.feature_tree import construct_feature, get_feature_by_key_or_name, \
    construct_features_from_configs

import ray.experimental

import ray
from ray.data import Dataset

import featurizer
import common
import client

# TODO these are local packages to pass to dev cluster
LOCAL_PACKAGES_TO_PASS_TO_REMOTE_DEV_RAY_CLUSTER = [featurizer, common, client]


class Featurizer:

    @classmethod
    def run(cls, config: FeaturizerConfig, ray_address: str, parallelism: int):
        features = construct_features_from_configs(config.feature_configs)
        # for f in features:
        #     print(f, f.children)

        storage = FeaturizerStorage()
        storage.store_features_metadata_if_needed(features)

        data_ranges_meta = storage.get_data_sources_meta(features, start_date=config.start_date, end_date=config.end_date)
        stored_features_meta = storage.get_features_meta(features, start_date=config.start_date, end_date=config.end_date)

        label_feature = None
        if config.label_feature is not None:
            if isinstance(config.label_feature, int):
                label_feature = features[config.label_feature]
            else:
                # TODO implement fetching feature by name
                raise NotImplementedError

        cache = {}
        features_to_store = [features[i] for i in config.features_to_store]

        with ray.init(address=ray_address, ignore_reinit_error=True, runtime_env={
            'py_modules': LOCAL_PACKAGES_TO_PASS_TO_REMOTE_DEV_RAY_CLUSTER,
            'pip': ['pyhumps', 'diskcache']
        }):
            # remove old actor from prev session if it exists
            try:
                cache_actor = get_cache_actor()
                ray.kill(cache_actor)
            except ValueError:
                pass

            cache_actor = create_cache_actor(cache)
            create_db_actor()
            # TODO pass params indicating if user doesn't want to join/lookahead and build/execute graph accordingly
            dag = build_feature_label_set_task_graph(
                features=features,
                label=label_feature,
                label_lookahead=config.label_lookahead,
                data_ranges_meta=data_ranges_meta,
                obj_ref_cache=cache,
                features_to_store=features_to_store,
                stored_feature_blocks_meta=stored_features_meta,
                result_owner=cache_actor
            )

            # TODO first two values are weird outliers for some reason, why?
            # df = df.tail(-2)
            refs = execute_graph(dag=dag, parallelism=parallelism)
            ray.get(cache_actor.record_featurizer_result_refs.remote(refs))

    @classmethod
    def get_dataset(cls) -> Dataset:
        cache_actor = get_cache_actor()
        refs = ray.get(cache_actor.get_featurizer_result_refs.remote())
        return ray.data.from_pandas_refs(refs)

    @classmethod
    def get_ds_metadata(cls, ds: Dataset) -> Dict:
        # should return metadata about featurization result e.g. in memory size, num blocks, schema, set name, etc.
        return {
            'count': ds.count(),
            'schema': ds.schema(),
            'num_blocks': ds.num_blocks(),
            'size_bytes': ds.size_bytes(),
            'stats': ds.stats()
        }

    @classmethod
    def get_columns(cls, ds: Dataset) -> List[str]:
        ds_metadata = cls.get_ds_metadata(ds)
        schema: pyarrow.Schema = ds_metadata['schema']
        cols = schema.names
        return cols

    @classmethod
    def get_feature_columns(cls, ds: Dataset) -> List[str]:
        columns = cls.get_columns(ds)
        label_column = cls.get_label_column(ds)
        res = []
        to_remove = ['timestamp', 'receipt_timestamp', label_column]
        for c in columns:
            if c not in to_remove:
                res.append(c)
        return res

    @classmethod
    def get_label_column(cls, ds: Dataset) -> str:
        cols = cls.get_columns(ds)
        print(cols)
        pos = None
        for i in range(len(cols)):
            if cols[i].startswith('label_'):
                if pos is not None:
                    raise ValueError('Can not have more than 1 label column')
                pos = i

        if pos is None:
            raise ValueError('Can not find label column')

        return cols[pos]

    @classmethod
    def get_materialized_data(cls, start: Optional[str] = None, end: Optional[str] = None, pick_every_nth_row: Optional[int] = 1) -> pd.DataFrame:
        cache_actor = get_cache_actor()
        refs = ray.get(cache_actor.get_featurizer_result_refs.remote())

        # TODO filter refs based on start/end
        @ray.remote
        def downsample(df: pd.DataFrame, nth_row: int) -> pd.DataFrame:
            return downsample_uniform(df, nth_row)

        if pick_every_nth_row != 1:
            # TODO const num_cpus ?
            downsampled_refs = [downsample.options(num_cpus=0.9).remote(ref, pick_every_nth_row) for ref in refs]
        else:
            downsampled_refs = refs

        downsampled_dfs = ray.get(downsampled_refs)
        return concat(downsampled_dfs)


if __name__ == '__main__':
    ray_address = 'ray://127.0.0.1:10001'
    with ray.init(address=ray_address, ignore_reinit_error=True, runtime_env={
        'py_modules': LOCAL_PACKAGES_TO_PASS_TO_REMOTE_DEV_RAY_CLUSTER,
        'pip': ['pyhumps']
    }):
        df = Featurizer.get_materialized_data()
        print(df)