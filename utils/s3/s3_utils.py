
import utils.concurrency.concurrency_utils as cu
import boto3
import functools
from typing import Tuple, List, Any, Optional
from utils.pandas.df_utils import load_and_cache
import pandas as pd

# _sessions_per_process = {}
# _lock = threading.Lock()


# def get_session():
#     # thread safe singleton
#     global _sessions_per_process, _lock
#     pid = os.getpid()
#     if pid not in _sessions_per_process:
#         with _lock:
#             _sessions_per_process[pid] = boto3.Session()
#     return _sessions_per_process[pid]


# TODO set up via env vars
# TODO improve perf, make thread-safe
# https://emasquil.github.io/posts/multithreading-boto3/
def get_session() -> boto3.Session:
    return boto3.session.Session()

def get_file_size_kb(path: str) -> int:
    bucket_name, key = _parse_path(path)
    session = _get_session()
    s3_resource = session.resource('s3')
    obj = s3_resource.Object(bucket_name, key)
    # obj = client.get_object(Bucket=bucket_name, Key=key)
    # more metadata is stored in object
    file_size = obj.content_length

    return int(file_size/1000.0)


def get_file_sizes_kb(paths: List[str]) -> List[int]:
    callables = [functools.partial(get_file_size_kb, path=path) for path in paths]
    return cu.run_concurrently(callables)


def _parse_path(path: str) -> Tuple[str, str]:
    # 's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE/instrument_type=spot/instrument_extra={}/symbol=BTC-USDT/base=BTC/quote=USDT/date=2022-06-11/compaction=raw/version=testing /file.gz.parquet'
    path = path.removeprefix('s3://')
    split = path.split('/')
    bucket_name = split[0]
    key = path.removeprefix(bucket_name + '/')
    return bucket_name, key


# TODO asyncify paginator https://gist.github.com/gudgud96/bdde37c9cc6b56a88ae3a7a0a217a723
# TODO multithreaded version https://gist.github.com/sjakthol/19367500519a8828ec77ef5d34b1b0b9
# TODO for threaded delete https://gist.github.com/angrychimp/76b8fe9f15c88d7f121db1cc5d2c215d
# TODO retriving common prefixes https://stackoverflow.com/questions/36991468/how-to-retrieve-bucket-prefixes-in-a-filesystem-style-using-boto3
# TODO parallel list https://joshua-robinson.medium.com/listing-67-billion-objects-in-1-bucket-806e4895130f
# TODO more https://gist.github.com/joshuarobinson/ecf4f82e5d935f841b94b8cccae7c990
# https://alukach.com/posts/tips-for-working-with-a-large-number-of-files-in-s3/

# for s3 inventory
# https://gist.github.com/alukach/1a2b8b6366410fb94fa5cee7f72ee304
# https://alukach.com/posts/parsing-s3-inventory-output/
def list_files(bucket_name: str, prefix: str = '', page_size: int = 1000, max_items: Optional[int] = None) -> List[Any]:
    session = _get_session()
    client = session.client('s3')
    paginator = client.get_paginator('list_objects') # TODO use list_objects_v2
    pagination_config = {'PageSize': page_size}
    if max_items:
        pagination_config['MaxItems'] = max_items
    iterator = paginator.paginate(
        Bucket=bucket_name,
        PaginationConfig=pagination_config,
        Prefix=prefix
    ) # TODO figure out Delimiter?

    res = []
    for obj in iterator:
        fetched = obj['Contents']
        keys = [f['Key'] for f in fetched]
        # filter names that match prefix
        res.extend(list(filter(lambda e: e != prefix, keys)))
    return res


def inventory() -> List[pd.DataFrame]:
    INVENTORY_BUCKET = 'inventory-reports-1'
    INVENTORY_PREFIX = 'svoe.test.1/test_inventory_config_1/data/'
    files = list_files(INVENTORY_BUCKET, INVENTORY_PREFIX)
    # append s3://bucket_name
    files = [f's3://{INVENTORY_BUCKET}/{f}' for f in files]
    print(files)
    return load_and_cache(files, './cached_dfs')




