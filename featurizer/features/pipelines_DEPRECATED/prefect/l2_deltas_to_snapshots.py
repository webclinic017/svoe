
from prefect import task, flow, unmapped
from prefect_dask.task_runners import DaskTaskRunner
from typing import List, Any, Optional

import featurizer.features.loader.loader as loader
import featurizer.features.loader.catalog as catalog
import featurizer.data.l2_book_incremental.cryptofeed.l2_snapshot_utils as l2u
import common.s3.s3_utils as s3u
import time
import pandas as pd

DASK_SCHEDULER_ADDRESS = 'tcp://127.0.0.1:60939'
DASK_NUM_WORKERS = 4
DASK_THREADS_PER_WORKER = 32
CHUNK_SIZE = 10 # number of files to treat as a single chunk/dataframe
COMPACTION_GROUP_SIZE = 20 # number of chunks to store in the same file


def get_compaction_groups(grouped_chunks: List[List[List[str]]], compaction_group_size: int) -> List[List[int]]:
    # TODO move this to utility class?
    # TODO make logic based on file size, not fixed compaction_group_size
    # we need to make sure not to compact together chunks from different groups
    #[[[a, b, c], [d, e], [f, g]], [[h, k], [l, n]], [[n, o], [p, q, r], [s, t]]]
    id = 0
    grouped_chunk_ids = []
    for group in grouped_chunks:
        grouped_ids = []
        for chunk in group:
            grouped_ids.append(id)
            id += 1
        grouped_chunk_ids.append(grouped_ids)
    # [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]]
    compaction_groups = []
    for grouped_ids in grouped_chunk_ids:
        compacted_ids = [grouped_ids[i:i + compaction_group_size] for i in range(0, len(grouped_ids), compaction_group_size)]
        compaction_groups.extend(compacted_ids)
    return compaction_groups


@task
def load_grouped_filenames_chunks(exchange: str, instrument_type: str, symbol: str) -> List[List[List[str]]]:
    filenames_groups, has_overlap = catalog.get_filenames_groups('l2_book', exchange, instrument_type, symbol)
    grouped_chunks = catalog.chunk_filenames_groups(filenames_groups, CHUNK_SIZE)
    return grouped_chunks


@task
def load_l2_deltas_chunk(index: int, chunks: List[List[str]]) -> pd.DataFrame:
    return loader.load_with_snapshot(index, chunks)


@task
def load_s3_chunk_metadata(index: int, chunks: List[List[str]]) -> List[int]:
    return s3u.get_file_sizes_kb(chunks[index])


@task
def gather_df_in_memory_sizes_info(dfs: List[pd.DataFrame]) -> Any:
    sizes_kb = list(map(lambda df: l2u.get_info(df)['df_size_kb'], dfs))
    return sizes_kb


@task
def gather_s3_metadata_info(sizes_kb: List[List[int]]) -> Any:
    return sizes_kb


@task
def transform_deltas_to_snapshots(deltas_df: pd.DataFrame) -> pd.DataFrame:
    # TODO
    time.sleep(1)
    return deltas_df


@task
def compact_and_store(ids: List[int], dfs: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
    # concatenate dataframes into one and store to data lake
    # use data wrangler
    # update index
    # TODO
    time.sleep(1)
    return None


def plot_loaded_data_info(info: Any):
    return # TODO


@task
def gather_results(results: List[Any]) -> Any:
    # TODO
    # gather pipeline stats
    time.sleep(1)
    return True


# @flow(task_runner=DaskTaskRunner(address=DASK_SCHEDULER_ADDRESS))
@flow(task_runner=DaskTaskRunner(
    cluster_kwargs={'n_workers': DASK_NUM_WORKERS, 'threads_per_worker': DASK_THREADS_PER_WORKER}
))
def l2_deltas_to_snapshots_flow(exchange: str, instrument_type: str, symbol: str, limit_chunks: int = None) -> Any:
    # load filenames
    grouped_chunks = load_grouped_filenames_chunks(exchange, instrument_type, symbol)
    compaction_groups = get_compaction_groups(grouped_chunks, COMPACTION_GROUP_SIZE)
    chunks = [chunk for group in grouped_chunks for chunk in group] # flatten
    chunks = chunks[0: limit_chunks]

    # map loaded dfs
    mapped_loaded_dfs = load_l2_deltas_chunk.map(range(len(chunks)), chunks=unmapped(chunks))
    # map loaded s3 metadata
    # mapped_s3_metadata = load_s3_chunk_metadata.map(range(len(chunks)), chunks=unmapped(chunks))

    # get in memory data info
    in_memory_data_info = gather_df_in_memory_sizes_info(mapped_loaded_dfs)
    # s3_metadata_info = gather_s3_metadata_info(mapped_s3_metadata)
    #
    # transform deltas to snaps
    # mapped_transformed_dfs = transform_deltas_to_snapshots.map(mapped_loaded_dfs)

    # store
    # results = compact_and_store.map(compaction_groups, dfs=unmapped(mapped_transformed_dfs))

    # gather stats
    # stats = gather_results(results)

    # return in_memory_data_info, s3_metadata_info, stats
    # return s3_metadata_info
    return in_memory_data_info

# def test():
#     filenames, has_overlap = catalog.get_sorted_filenames('l2_book', 'BINANCE', 'spot', 'BTC-USDT')
#     filenames = filenames[0:100]
#
#     # start1 = time.time()
#     # dfs1 = dfu.load_df(filenames, len(filenames))
#     # delta1 = time.time() - start1
#     # print(f'Delta 1 {delta1}')
#     start2 = time.time()
#     dfs2 = dfu.load_files(filenames)
#     delta2 = time.time() - start2
#     print(f'Delta 2 {delta2}')

if __name__ == "__main__":
    print(l2_deltas_to_snapshots_flow('BINANCE', 'spot', 'BTC-USDT', 10))

