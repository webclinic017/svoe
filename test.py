import sys

# TODO move to PYTHONPATH
# sys.path.append('/Users/anov/IdeaProjects/cryptofeed')
# sys.path.append('/Users/anov/IdeaProjects/cryptostore')
# sys.path.append('/dask_cluster/')

from configs.data_feed.kubernetes_config_builder import KubernetesConfigBuilder
from configs.data_feed.cryptostore_config_builder import CryptostoreConfigBuilder
from configs.data_feed.base_config_builder import BaseConfigBuilder
from data_feed.data_feed_service import DataFeedService
from cryptofeed import FeedHandler
from cryptofeed.defines import TICKER
from cryptofeed.exchanges import Coinbase
from cryptofeed.callback import TickerCallback
from prometheus_client import start_http_server, multiprocess

def test_datafeed():
    #
    # kcb = KubernetesConfigBuilder()
    # print(kcb.gen())
    ccb = CryptostoreConfigBuilder()
    print(ccb.gen_DEBUG())
    DataFeedService.run()
    # read_s3()
    # start_http_server(8000)
    # fh = FeedHandler()
    # ticker_cb = {TICKER: TickerCallback(None)}
    # fh.add_feed(Coinbase(symbols=['BTC-USD'], channels=[TICKER], callbacks=ticker_cb))
    # fh.run()

# To rebuild Cython https://stackoverflow.com/questions/34928001/distutils-ignores-changes-to-setup-py-when-building-an-extension
# python setup.py clean --all
# python setup.py develop
if __name__ == '__main__':
    test_datafeed()