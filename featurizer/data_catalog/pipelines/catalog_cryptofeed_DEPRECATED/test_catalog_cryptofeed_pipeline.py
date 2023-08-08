import itertools
import time
import unittest

import ray

from featurizer.data_catalog.pipelines.catalog_cryptotick.tasks import make_catalog_item
from featurizer.data_catalog import CatalogCryptofeedDag
from featurizer.data_catalog import PipelineRunner
from featurizer.sql.client import FeaturizerMysqlClient
from featurizer.data_catalog.common.utils.cryptofeed.utils import generate_cryptofeed_input_items
from utils.pandas.df_utils import load_dfs


class TestCatalogCryptofeedPipeline(unittest.TestCase):

    # TODO util this
    def test_parse_s3_keys(self):
        # TODO add multiproc
        batch_size = 1000
        exchange_symbol_unique_pairs = set()
        print('Loading generator...')
        generator = generate_cryptofeed_input_items(batch_size)
        print('Generator loaded')
        for _ in range(5):
            batch = next(generator)
            for i in batch:
                exchange_symbol_unique_pairs.add((i['exchange'], i['symbol']))
        print(exchange_symbol_unique_pairs)

    def test_db_client(self):
        batch_size = 2
        print('Loading generator...')
        generator = generate_cryptofeed_input_items(batch_size)
        print('Generator loaded')
        batch = next(generator)
        client = MysqlClient()
        client.create_tables()
        _, not_exist = client.filter_cryptofeed_batch(batch)
        print(not_exist)
        print(f'Found {batch_size - len(not_exist)} items in db, {len(not_exist)} to write')
        dfs = load_dfs([i['path'] for i in not_exist])
        catalog_items = []
        for df, i in zip(dfs, not_exist):
            catalog_items.append(make_catalog_item(df, i))
        write_res = client.write_catalog_item_batch(catalog_items)
        print(f'Written {len(catalog_items)} to db, checking again...')
        _, not_exist = client.filter_cryptofeed_batch(batch)
        print(f'Found {batch_size - len(not_exist)} existing records in db')
        assert len(not_exist) == 0


    def test_pipeline(self):
        with ray.init(address='auto'):
            batch_size = 10
            num_batches = 5
            runner = PipelineRunner()
            runner.run(CatalogCryptofeedDag())
            print('Inited runner')
            print('Loading generator...')
            generator = generate_cryptofeed_input_items(batch_size)
            print('Generator loaded')
            print('Queueing batch...')
            inputs = []
            for i in range(num_batches):
                input_batch = next(generator)
                inputs.append(input_batch)
                runner.pipe_input(input_batch)
                print(f'Queued {i + 1} batches')
            print('Done queueing')
            # wait for everything to process

            # TODO this quits early if job is long
            # TODO make wait_for_completion func
            time.sleep(720)

            # check if index was written to db
            client = FeaturizerMysqlClient()
            not_exist = client.filter_cryptofeed_batch(list(itertools.chain(*inputs)))
            # TODO should be 0
            print(len(not_exist))

if __name__ == '__main__':
    t = TestCatalogCryptofeedPipeline()
    t.test_pipeline()
    # t.test_db_client()

