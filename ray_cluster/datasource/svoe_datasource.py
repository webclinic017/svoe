from typing import Any, Dict, List, Optional
from ray.data.datasource.datasource import Datasource, Reader
from ray_cluster.datasource.svoe_datasource_reader import SvoeDatasourceReader
# TODO use https://github.com/matplotlib/mplfinance

class SvoeDatasource(Datasource):
    def create_reader(
        self, file_paths: List[str]
    ) -> Reader:
        return SvoeDatasourceReader(file_paths)

    # TODO wrties