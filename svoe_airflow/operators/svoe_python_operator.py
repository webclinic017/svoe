
from typing import Dict, Any, Collection, Mapping

from common.common_utils import get_callable_from_remote_code_file
from airflow.utils.context import Context
from common.s3.s3_utils import download_file
from airflow.models import BaseOperator

from svoe_airflow.operators.require_cluster_mixin import RequireClusterMixin


# https://github.com/anyscale/airflow-provider-ray/blob/main/ray_provider/decorators/ray_decorators.py
class SvoePythonOperator(BaseOperator): # TODO does this need RequireClusterMixin?

    # re args https://github.com/ajbosco/dag-factory/issues/121

    def __init__(
        self,
        args: Dict,
        op_args: Collection[Any] | None = None,
        op_kwargs: Mapping[str, Any] | None = None,
        **kwargs
    ):
        BaseOperator.__init__(self, **kwargs)
        # RequireClusterMixin.__init__(self, args=args)
        self.remote_code_remote_path = args['_remote_code_remote_path'] # TODO sync with client keys
        self.op_args = op_args or ()
        self.op_kwargs = op_kwargs or {}
        self.python_callable = None

    def execute(self, context: Context) -> Any:
        temp_dir, python_file_path = download_file(self.remote_code_remote_path)
        if self.python_callable is None:
            self.python_callable = get_callable_from_remote_code_file(python_file_path)
        temp_dir.cleanup()
        return self.python_callable(*self.op_args, **self.op_kwargs)


if __name__ == '__main__':
    python_file_path = '/Users/anov/svoe_junk/py_files/test_remote_code_v1.py'
    _callable = get_callable_from_remote_code_file(python_file_path)
    _callable('a')

