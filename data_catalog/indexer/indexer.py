from typing import List, Dict, Optional

import pandas as pd
import ray

import utils.s3.s3_utils as s3_utils
from data_catalog.indexer.sql.client import MysqlClient

# for pipelined queue https://docs.ray.io/en/latest/ray-core/patterns/pipelining.html
# for backpressure https://docs.ray.io/en/latest/ray-core/patterns/limit-pending-tasks.html
# fro mem usage https://docs.ray.io/en/releases-1.12.0/ray-core/objects/memory-management.html
# memory monitor https://docs.ray.io/en/latest/ray-core/scheduling/ray-oom-prevention.html

# TODO this should be in separate class to avoid circular deps
InputItem = Dict
InputItemBatch = List[InputItem]
IndexItem = Dict
IndexItemBatch = List[IndexItem]

@ray.remote
class Coordinator:
    WRITE_BATCH_SIZE = 1000

    input_queue: List[InputItemBatch] = [] # batches of input items, should be checked for existence in Db
    indexable_input_queue: List[InputItem] = [] # non existent input items which should be indexed and ready to download
    to_index_queue: List[pd.DataFrame] = [] # downloaded object refs # TODO or ObjectRefs?
    to_write_index_queue: List[IndexItem] = [] # index items ready wo be written to Db

    def get_input_batch(self) -> Optional[List[InputItem]]:
        if len(self.input_queue) != 0:
            return self.input_queue.pop(0)
        else:
            return None

    def put_indexable_items(self, batch: InputItemBatch):
        self.indexable_input_queue.extend(batch)

    def get_to_write_batch(self) -> Optional[IndexItemBatch]:
        # TODO check if this is the last batch
        if len(self.to_write_index_queue) < self.WRITE_BATCH_SIZE:
            return None
        else:
            return self.to_write_index_queue[-self.WRITE_BATCH_SIZE:]

    def update_progress(self, info: Dict):
        # TODO
        return

    # main coordinator loop
    def run(self):
        # TODO add backpressure to Driver program, stop when driver queue is empty
        while True:
            # TODO if remote() call blocks, everything below should be separated
            if len(self.indexable_input_queue) != 0:
                to_download = self.indexable_input_queue.pop(0)
                load_and_queue_df.remote(to_download, self.to_index_queue)
            if len(self.to_index_queue) != 0:
                # TODO batch this?
                to_index = self.to_index_queue.pop(0)
                index_and_queue_df.remote(to_index, self.to_write_index_queue)

            # TODO add queues status report here to show on a dashboard (Streamlit?)


@ray.remote
class DbReader:
    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator
        self.client = MysqlClient()

    def check_exists(self, batch: List[InputItem]) -> List[InputItem]:
        # TODO
        return []

    def run(self):
        self.work_item_ref = self.coordinator.get_input_batch.remote()
        while True:
            work_item = ray.get(self.work_item_ref)
            if work_item is None:
                # TODO add sleep so we don't waste CPU cycles
                continue

            # schedule async fetching of next work item to enable compute pipelining
            self.work_item_ref = self.coordinator.get_input_batch.remote()
            # work item is a batch of input items to check if they are already indexed
            non_existent = self.check_exists(work_item)
            # TODO do we call ray.get here?
            self.coordinator.put_indexable_items(non_existent).remote()


@ray.remote
class DbWriter:
    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator
        self.client = MysqlClient()

    def write_batch(self, batch: List[IndexItem]) -> Dict:
        self.client.create_tables()
        self.client.write_index_items(batch)
        return {}

    def run(self):
        self.work_item_ref = self.coordinator.get_to_write_batch.remote()
        while True:
            work_item = ray.get(self.work_item_ref)
            if work_item is None:
                # TODO sleep here for some time to avoid waisting CPU cycles?
                continue

            # schedule async fetching of next work item to enable compute pipelining
            self.work_item_ref = self.coordinator.get_to_write_batch.remote()
            # work item is a batch of index items to write to DB
            write_status = self.write_batch(work_item)
            # TODO do we call ray.get here?
            self.coordinator.update_progress(write_status).remote()


# TODO set CPU=0, or add parallelism resource
@ray.remote
def load_df(path: str) -> pd.DataFrame:
    return s3_utils.load_df(path)


# TODO set CPU=0, or add parallelism resource
@ray.remote
def load_and_queue_df(path: str, queue: List):
    df = ray.get(load_df.remote(path))
    queue.append(df)


@ray.remote
def calculate_meta(df: pd.DataFrame) -> IndexItem:
    # TODO
    return {}


# TODO add batching?
@ray.remote
def index_and_queue_df(df: pd.DataFrame, queue: List):
    index_item = ray.get(calculate_meta.remote(df))
    queue.append(index_item)


def generate_input_items() -> List[InputItemBatch]:
    inv = s3_utils.inventory()
    return []


