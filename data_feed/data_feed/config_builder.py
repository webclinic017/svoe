import yaml
import numpy
import math
from pathlib import Path
from typing import Any
from cryptofeed.symbols import gen_symbols
from cryptofeed.defines import BINANCE, COINBASE, KRAKEN, HUOBI, DERIBIT, BITMEX

MEDIUM = 'kafka' # 'redis' or 'kafka'

CONFIG_PATH = str(Path(__file__).parent / 'configs/cryptostore_config.yaml')
AWS_CREDENTIALS_PATH = str(Path(__file__).parent / 'configs/aws_credentials.yaml')

class ConfigBuilder(object):

    def __init__(self, exchanges: list[str]):
        self.exchanges = exchanges
        self.exchanges_config = {
            # pair_gen, max_depth_l2, include_ticker
            BINANCE : [self._get_binance_pairs()[:6], 100, True], #max_depth 5000 # https://github.com/bmoscon/cryptostore/issues/156 set limit to num pairs to avoid rate limit?
            COINBASE: [self._get_coinbase_pairs()[:2], 100, True],
            KRAKEN: [self._get_kraken_pairs()[:1], 100, True], #max_depth 1000
            HUOBI: [self._get_huobi_pairs()[:1], 100, False],
            # 'BITMEX' : BITMEX,
            # 'DERIBIT' : DERIBIT
        }

    def pairs_to_kuber_pods(self) -> dict[int, dict[str, list[str]]]:

        # e1: p1 p2 p3 p4 p5 p6  | pairs: 6 cost: 3.6 round: 3
        #
        # e2: p1 p2 | pairs: 2 cost: 1.2 round: 1
        #
        # e3: p1 | pairs: 1 cost: 0.6 round: 1
        #
        # e4: p1 | pairs: 1 cost: 0.6 round: 1
        #
        # num_pods = 6

        num_pods = 10
        pods = [*range(0, num_pods)]
        num_exchanges = len(self.exchanges_config)
        num_pairs = sum(len(val[0]) for val in self.exchanges_config.values())

        if num_pairs < num_pods:
            raise Exception('Can not have more pods: [{}] then pairs: [{}]'.format(num_pods, num_pairs))

        if num_pods > num_exchanges:
            # assign pods to exchanges
            ex_to_pods = {}

            # calc how many pods on average we need for a pair
            pods_per_pair = num_pods/num_pairs

            # distribute pods for each exchage
            for ex in self.exchanges_config.keys():
                pods_needed = pods_per_pair * len(self.exchanges_config[ex][0])

                # round down, distribute leftovers later
                round = math.floor(pods_needed)

                # exchange needs only 1 pod
                if round == 0 :
                    round = 1

                ex_to_pods[ex] = []
                while round > 0:
                    ex_to_pods[ex].append(pods.pop(0))
                    round -= 1

            # round robin leftovers
            while len(pods) > 0:
                # find exchange with largest residual of needed capacity and assign a pod
                _max = max(ex_to_pods.items(), key = lambda x: pods_per_pair * len(self.exchanges_config[x[0]][0]) - len(ex_to_pods[x[0]]))
                ex_to_pods[_max[0]].append(pods.pop(0))

            # distribute pairs to pods
            pods_to_pairs = {}
            for ex in ex_to_pods.keys():
                pairs = self.exchanges_config[ex][0]
                assigned_pods = ex_to_pods[ex]
                split = numpy.array_split(pairs, len(assigned_pods))
                for i in range(len(assigned_pods)):
                    ex_to_pairs = {}
                    ex_to_pairs[ex] = split[i].tolist()
                    pods_to_pairs[assigned_pods[i]] = ex_to_pairs

            return pods_to_pairs

        else:
            ex_pairs_tuple_list = []
            for ex in self.exchanges_config.keys():
                pairs = self.exchanges_config[ex][0]
                for pair in pairs:
                    ex_pairs_tuple_list.append((ex,pair))

            split = numpy.array_split(ex_pairs_tuple_list, num_pods)

            # distribute pairs to pods
            pods_to_pairs = {}
            for i in range(num_pods):
                pod = pods[i]
                pods_to_pairs[pod] = {}
                for ex_pair_tuple in split[i].tolist():
                    ex = ex_pair_tuple[0]
                    pair = ex_pair_tuple[1]
                    if ex in pods_to_pairs[pod]:
                        pods_to_pairs[pod][ex].append(pair)
                    else:
                        pods_to_pairs[pod][ex] = [pair]

            return pods_to_pairs

    # TODO refactor dict() -> {} and list() -> [] for consistency
    def build_cryptostore_config(self) -> str:
        aws_credentials = self._read_aws_credentials()
        data = dict(
            cache=MEDIUM,
            # https://stackoverflow.com/questions/52996028/accessing-local-kafka-from-within-services-deployed-in-local-docker-for-mac-inc
            kafka=dict(
                # ip='host.docker.internal', # for Docker on Mac use host.docker.internal:19092
                # port=19092,
                ip='127.0.0.1',
                port=9092,
                start_flush=True,
            ),
            redis=dict(
                ip='127.0.0.1',
                port=6379,
                socket=None,
                del_after_read=True,
                retention_time=None,
                start_flush=True,
            ),
            storage=['parquet'],
            storage_retries=5,
            storage_retry_wait=30,
            parquet=dict(
                del_file=True,
                append_counter=0,
                file_format=['exchange', 'symbol', 'data_type', 'timestamp'],
                compression=dict(
                    codec='BROTLI',
                    level=6,
                ),
                prefix_date=True,
                S3=dict(
                    key_id=aws_credentials[0],
                    secret=aws_credentials[1],
                    bucket=aws_credentials[2],
                    prefix='parquet'
                ),
                # path=TEMP_FILES_PATH,
            ),
            storage_interval=90,
            exchanges=self._build_exchanges_config()
        )

        with open(CONFIG_PATH, 'w+') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)

        return CONFIG_PATH

    def _build_exchanges_config(self) -> dict[str, Any]:
        config = dict()
        for exchange in self.exchanges:
            if exchange not in self.exchanges_config:
                raise Exception('Exchange {} is not supported'.format(exchange))

            # pairs
            pairs = self.exchanges_config[exchange][0]

            # book
            l2_book = dict(
                symbols=pairs,
                book_delta=True,
            )
            max_depth = self.exchanges_config[exchange][1]
            if max_depth > 0:
                l2_book['max_depth'] = max_depth

            config[exchange] = dict(
                retries=-1,
                l2_book=l2_book,
                trades=pairs,
            )

            include_ticker = self.exchanges_config[exchange][2]

            if include_ticker:
                config[exchange]['ticker'] = pairs

        return config

    # TODO refactor below to remove dependency on exchnage specific logic
    @staticmethod
    def _get_kraken_pairs() -> list[str]:
        symbols = gen_symbols(KRAKEN)

        # USD quote only
        return [*filter(lambda item: item.split('-')[1] == 'USD', list(symbols.keys()))]

    @staticmethod
    def _get_coinbase_pairs() -> list[str]:
        symbols = gen_symbols(COINBASE)

        # USD quote only
        return [*filter(lambda item: item.split('-')[1] == 'USD', list(symbols.keys()))]

        # from ccxt
        # c = coinbase()
        # markets = c.fetch_markets()
        # usd_only = list(filter(lambda item: item['symbol'].split('/')[1] == 'USD', markets))
        # usd_only_symbols = list(map(lambda item: item['symbol'], usd_only))

        # return usd_only_symbols

    @staticmethod
    def _get_binance_pairs() -> list[str]:
        symbols = gen_symbols(BINANCE)

        # USD quote only
        return [*filter(lambda item: item.split('-')[1] == 'USDT', list(symbols.keys()))]

    @staticmethod
    def _get_huobi_pairs() -> list[str]:
        symbols = gen_symbols(HUOBI)

        # USD quote only
        return [*filter(lambda item: item.split('-')[1] == 'USDT', list(symbols.keys()))]

    @staticmethod
    def get_deribit_pairs():
        symbols = gen_symbols(DERIBIT)
        print(symbols)


    @staticmethod
    def get_bitmex_pairs():
        symbols = gen_symbols(BITMEX)
        print(symbols)

    @staticmethod
    def _read_aws_credentials() -> list[str]:
        with open(AWS_CREDENTIALS_PATH) as file:
            data = yaml.load(file, Loader = yaml.FullLoader)

        return [data['key_id'], data['secret'], data['bucket']]
