import ray

from data_catalog.indexer.actors.coordinator import Coordinator
from data_catalog.indexer.actors.db import DbReader, DbWriter
from data_catalog.indexer.actors.queues import DownloadQueue, StoreQueue, InputQueue

# for pipelined queue https://docs.ray.io/en/latest/ray-core/patterns/pipelining.html
# for backpressure https://docs.ray.io/en/latest/ray-core/patterns/limit-pending-tasks.html
# fro mem usage https://docs.ray.io/en/releases-1.12.0/ray-core/objects/memory-management.html
# memory monitor https://docs.ray.io/en/latest/ray-core/scheduling/ray-oom-prevention.html
from data_catalog.indexer.util import generate_input_items

INPUT_ITEM_BATCH_SIZE = 2
WRITE_INDEX_ITEM_BATCH_SIZE = 1000


class Indexer:
    def run(self):

        # init queue actors
        input_queue = InputQueue.remote()
        download_queue = DownloadQueue.remote()
        store_queue = StoreQueue.remote()

        # init coordinator
        coordintator = Coordinator.remote(download_queue, store_queue)

        # init db actors
        num_db_readers = 4
        num_db_writers = 4
        db_readers = [DbReader.remote(input_queue, download_queue) for _ in range(num_db_readers)]
        for r in db_readers:
            r.run.remote()
        db_writers = [DbWriter.remote(coordintator, store_queue) for _ in range(num_db_writers)]
        for w in db_writers:
            w.run.remote()
        coordintator.run.remote()

        # pipe input
        # TODO add throughput limit, backpressure
        # for input_batch in generate_input_items(INPUT_ITEM_BATCH_SIZE):
        for _ in range(2):
            input_batch = next(generate_input_items(INPUT_ITEM_BATCH_SIZE))
            ray.get(input_queue.put.remote(input_batch))
