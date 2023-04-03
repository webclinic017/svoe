from typing import List, Any

import pandas as pd
import ray
from ray import workflow
from streamz import Stream

from data_catalog.common.actors.db import DbActor
from data_catalog.common.actors.stats import Stats
from data_catalog.common.data_models.models import InputItemBatch
from data_catalog.common.tasks.tasks import filter_existing, gather_and_wait, load_df, catalog_df, chain_no_ret, \
    write_batch, store_df
from data_catalog.common.utils.register import ray_task_name, send_events_to_stats, EventType
from data_catalog.pipelines.dag import Dag
from featurizer.features.data.l2_book_incremental.cryptotick.cryptotick_l2_book_incremental import \
    CryptotickL2BookIncrementalData
from featurizer.features.data.l2_book_incremental.cryptotick.utils import preprocess_l2_inc_df
from featurizer.features.definitions.l2_snapshot.l2_snapshot_fd import L2SnapshotFD
from ray_cluster.testing_utils import mock_feature
from utils.pandas.df_utils import gen_split_df_by_mem, concat


class CatalogCryptotickDag(Dag):

    def get(self, workflow_id: str, input_batch: InputItemBatch, stats: Stats, db_actor: DbActor):
        # TODO filter?
        download_task_ids = []
        catalog_task_ids = []
        store_task_ids = []
        extras = []
        store_tasks = []
        catalog_tasks = []
        items = input_batch[1]

        for i in range(len(items)):
            item = items[i]
            raw_size_kb = item['size_kb']
            extra = {'size_kb': raw_size_kb}
            extras.append(extra)

            download_task_id = f'{workflow_id}_{ray_task_name(load_df)}_{i}'
            download_task_ids.append(download_task_id)
            download_task = load_df.options(**workflow.options(task_id=download_task_id), num_cpus=0.001).bind(item,
                                                                                                               stats=stats,
                                                                                                               task_id=download_task_id,
                                                                                                               extra=extra)

            # TODO ids for split tasks
            split_task_id = f'{workflow_id}_{ray_task_name(split_l2_inc_df)}_{i}'
            splits = workflow.continuation(split_l2_inc_df.options(**workflow.options(task_id=split_task_id), num_cpus=0.9).bind(download_task, item['raw_date']))
            for j in range(len(splits)):
                split = splits[j]
                new_size_kb = raw_size_kb/len(splits)
                extra['size_kb'] = new_size_kb
                item['size_kb'] = new_size_kb

                # remove raw path so it is constructed when making catalog item
                del item['path']
                catalog_task_id = f'{workflow_id}_{ray_task_name(catalog_df)}_{j}_{i}'
                catalog_task_ids.append(catalog_task_id)
                catalog_task = catalog_df.options(**workflow.options(task_id=catalog_task_id), num_cpus=0.9).bind(split,
                                                                                                               item,
                                                                                                               stats=stats,
                                                                                                               task_id=catalog_task_id,
                                                                                                               source='cryptotick',
                                                                                                               extra=extra)
                catalog_tasks.append(catalog_task)

                store_task_id = f'{workflow_id}_{ray_task_name(store_df)}_{j}_{i}'
                store_task_ids.append(store_task_id)
                store_task = store_df.options(**workflow.options(task_id=store_task_id), num_cpus=0.01).bind(split,
                                                                                                             catalog_task,
                                                                                                             stats=stats,
                                                                                                             task_id=store_task_id,
                                                                                                             extra=extra)
                store_tasks.append(store_task)

        # report scheduled events to stats
        scheduled_events_reported = gather_and_wait.bind([
            send_events_to_stats.bind(stats, download_task_ids, ray_task_name(load_df), EventType.SCHEDULED, extras),
        ])

        # wait for store and catalog to EACH complete synchronously
        gathered_catalog_items = gather_and_wait.bind(catalog_tasks)
        gathered_store_tasks = gather_and_wait.bind(store_tasks)
        # TODO verify all is stored successfully here?
        # TODO make sure ALL catalog AND store complete synchronously?
        node = chain_no_ret.bind(gathered_catalog_items, gathered_store_tasks, scheduled_events_reported)

        write_catalog_task_id = f'{workflow_id}_{ray_task_name(write_batch)}'
        dag = write_batch.options(**workflow.options(task_id=write_catalog_task_id), num_cpus=0.01).bind(db_actor,
                                                                                                 node,
                                                                                                 stats=stats,
                                                                                                 task_id=write_catalog_task_id)

        return dag


# TODO resource spec
# TODO register for stats report and pass extra params
@ray.remote
def split_l2_inc_df(df: pd.DataFrame, raw_date_str: str) -> List[pd.DataFrame]:
    return split_l2_inc_df_and_pad_with_snapshot(df, 100 * 1024, raw_date_str)


# splits big L2 inc df into chunks, adding full snapshot to the beginning of each chunk
def split_l2_inc_df_and_pad_with_snapshot(df: pd.DataFrame, split_size_kb: int, raw_date_str: str) -> List[pd.DataFrame]:
    print('split started')
    print('preproc started')
    df = preprocess_l2_inc_df(df, raw_date_str)
    print('preproc finished')
    gen = gen_split_df_by_mem(df, split_size_kb)
    res = []
    prev_snap = None
    i = 0
    for split in gen:
        if i > 0:
            # TODO make sure snap ts is synthetic - between actual snap ts and split first ts
            split = prepend_snap(split, prev_snap)
        snap = run_l2_snapshot_stream(split)
        res.append(split)
        prev_snap = snap
        i += 1

    print('split finished')
    return res

# TODO typing
def run_l2_snapshot_stream(l2_inc_df: pd.DataFrame) -> Any:
    events = CryptotickL2BookIncrementalData.parse_events(l2_inc_df)
    source = Stream()

    # cryptotick stores 5000 depth levels
    feature_params = {'dep_schema': 'cryptotick', 'depth': 5000}
    out = L2SnapshotFD.stream({mock_feature(0): source}, feature_params)

    last_snap = [None]
    def set_last_snap(snap):
        last_snap[0] = snap

    out.sink(set_last_snap)

    for event in events:
        source.emit(event)

    return last_snap[0]

def prepend_snap(df: pd.DataFrame, snap) -> pd.DataFrame:
    # TODO inc this
    ts = snap['timestamp']
    receipt_ts = snap['receipt_timestamp']

    # make sure start of this block differs from prev
    microsec = 0.000001
    ts += microsec
    receipt_ts += microsec

    if ts >= df.iloc[0]['timestamp'] or receipt_ts >= df.iloc[0]['receipt_timestamp']:
        raise ValueError('Unable to shift snapshot ts when prepending')

    df_bids = pd.DataFrame(snap['bids'], columns=['price', 'size'])
    df_bids['side'] = 'bid'
    df_asks = pd.DataFrame(snap['asks'], columns=['price', 'size'])
    df_asks['side'] = 'ask'
    df_snap = concat([df_bids, df_asks])
    df_snap['update_type'] = 'SNAPSHOT'
    df_snap['timestamp'] = ts
    df_snap['receipt_timestamp'] = receipt_ts

    return concat([df_snap, df])

