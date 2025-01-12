from typing import Dict, List, Any, Tuple
import pandas as pd
from portion import Interval, closed, IntervalDict

from common.pandas.df_utils import is_ts_sorted, sub_df_ts
from common.time.utils import convert_str_to_seconds, round_float
from featurizer.sql.models.data_source_block_metadata import DataSourceBlockMetadata

# TODO deprecate this, use FeatureBlockMetadata and DataSourceBlockMetadata objects
BlockMeta = Dict # represents block metadata: name, time range, size, etc.
BlockRangeMeta = List[BlockMeta] # represents metadata of consecutive blocks

Block = pd.DataFrame
BlockRange = List[Block] # represents consecutive blocks

# TODO common consts for start_ts, end_ts, etc


def meta_to_interval(meta: BlockMeta) -> Interval:
    start = round_float(float(meta[DataSourceBlockMetadata.start_ts.name]))
    end = round_float(float(meta[DataSourceBlockMetadata.end_ts.name]))
    if start > end:
        raise ValueError('start_ts cannot be greater than end_ts')
    return closed(start, end)


def range_meta_to_interval(range_meta: BlockRangeMeta) -> Interval:
    start = round_float(float(range_meta[0][DataSourceBlockMetadata.start_ts.name]))
    end = round_float(float(range_meta[-1][DataSourceBlockMetadata.end_ts.name]))
    if start > end:
        raise ValueError('start_ts cannot be greater than end_ts')
    return closed(start, end)


def interval_to_meta(interval: Interval) -> BlockMeta:
    return {
        DataSourceBlockMetadata.start_ts.name: interval.lower,
        DataSourceBlockMetadata.end_ts.name: interval.upper,
    }


def ranges_to_interval_dict(ranges: List[BlockRangeMeta]) -> IntervalDict:
    res = IntervalDict()
    for range in ranges:
        interval = range_meta_to_interval(range)
        if overlaps_keys(interval, res):
            raise ValueError(f'Overlapping intervals for {interval}')

        res[interval] = range

    return res


def overlaps_keys(interval: Interval, d: IntervalDict) -> bool:
    keys = list(d.keys())
    for i in keys:
        if i.overlaps(interval):
            return True
    return False


def mock_meta(start_ts, end_ts, extra=None) -> BlockMeta:
    res = {
        DataSourceBlockMetadata.start_ts.name: float(start_ts),
        DataSourceBlockMetadata.end_ts.name: float(end_ts)
    }

    if extra:
        res.update(extra)
    return res


def make_ranges(data: List[BlockMeta]) -> List[BlockRangeMeta]:
    # TODO validate ts sorting

    # if consecutive blocks differ no more than this, they are in the same range
    # TODO should this be const per data_type?
    SAME_RANGE_DIFF_S = 1
    ranges = []
    cur_range = []
    for i in range(len(data)):
        cur_range.append(data[i])
        if i < len(data) - 1 and float(data[i + 1][DataSourceBlockMetadata.start_ts.name]) - float(data[i][DataSourceBlockMetadata.end_ts.name]) > SAME_RANGE_DIFF_S:
            ranges.append(cur_range)
            cur_range = []

    if len(cur_range) != 0:
        ranges.append(cur_range)

    return ranges


def identity_grouping(ranges: List[BlockMeta]) -> IntervalDict:
    # groups blocks 1 to 1
    res = IntervalDict()
    for meta in ranges:
        res[meta_to_interval(meta)] = [meta]
    return res


def windowed_grouping(ranges: List[BlockMeta], window: str) -> IntervalDict:
    res = IntervalDict()
    for i in range(len(ranges)):
        windowed_blocks = [ranges[i]]
        # look back until window limit is reached
        j = i - 1
        while j >= 0 and float(ranges[i]['start_ts']) - float(ranges[j]['end_ts']) <= convert_str_to_seconds(window):
            windowed_blocks.append(ranges[j])
            j -= 1
        res[meta_to_interval(ranges[i])] = windowed_blocks

    return res


def get_overlaps(key_intervaled_value: Dict[Any, IntervalDict]) -> Dict[Interval, Dict]:
    # TODO add visualization?
    # https://github.com/AlexandreDecan/portion
    # https://stackoverflow.com/questions/40367461/intersection-of-two-lists-of-ranges-in-python
    d = IntervalDict()
    # print(key_intervaled_value)
    first_key = list(key_intervaled_value.keys())[0]
    for interval, values in key_intervaled_value[first_key].items():
        d[interval] = {first_key: values}  # named_intervaled_values_dict

    # join intervaled_values_dict for each key with first to find all possible intersecting intervals
    # and their corresponding values
    for key, intervaled_values_dict in key_intervaled_value.items():
        if key == first_key:
            continue

        def concat(named_intervaled_values_dict, values):
            # TODO copy.deepcopy?
            res = named_intervaled_values_dict.copy()
            res[key] = values
            return res

        combined = d.combine(intervaled_values_dict, how=concat)  # outer join
        d = combined[d.domain() & intervaled_values_dict.domain()]  # inner join

    # make sure all intervals are closed
    res = {}
    for interval, value in d.items():
        res[closed(interval.lower, interval.upper)] = value
    return res


# TODO test this
def prune_overlaps(overlaps: Dict[Interval, Dict[Any, List]]) -> Dict[Interval, Dict[Any, List]]:
    for interval in overlaps:
        ranges = overlaps[interval]
        for key in ranges:
            range = ranges[key]
            pruned = []
            for e in range:
                if isinstance(e, Tuple):
                    if interval.overlaps(e[0]):
                        pruned.append(e)
                elif isinstance(e, BlockMeta):
                    if interval.overlaps(meta_to_interval(e)):
                        pruned.append(e)
                else:
                    raise ValueError(f'Unknown element type {type(e)}')

            if len(pruned) == 0:
                raise ValueError(f'Unable to prune key {key}')
            ranges[key] = pruned
    return overlaps


def lookahead_shift(df: pd.DataFrame, lookahead: str) -> pd.DataFrame:
    if not is_ts_sorted(df):
        raise ValueError('Can not lookahead shift not sorted df')
    lookahead_s = convert_str_to_seconds(lookahead)
    if lookahead_s < 1:
        raise ValueError('Lookahead interval should be more than 1s')
    cols = list(df.columns)
    cols.remove('timestamp')
    if 'receipt_timestamp' in cols:
        cols.remove('receipt_timestamp')
    df['lookahead_timestamp'] = df['timestamp'] + lookahead_s
    shifted = pd.merge_asof(df, df, left_on='lookahead_timestamp', right_on='timestamp', direction='backward')
    cols_new = [f'{c}_y' for c in cols]
    res_df = shifted[cols_new]
    res_df.insert(0, 'timestamp', shifted['timestamp_x'])
    if 'receipt_timestamp' in shifted:
        res_df.insert(0, 'receipt_timestamp', shifted['receipt_timestamp_x'])
    res_df = res_df.rename(columns=dict(zip(cols_new, cols)))
    start_ts = df.iloc[0]['timestamp']
    end_ts = df.iloc[-1]['timestamp'] - lookahead_s
    return sub_df_ts(res_df, start_ts, end_ts)


def is_sorted_intervals(intervals: List[Interval]) -> bool:
    for i in range(1, len(intervals)):
        if intervals[i - 1].upper > intervals[i].lower:
            return False
    return True


def merge_asof_multi(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    res = dfs[0]
    for i in range(1, len(dfs)):
        res = pd.merge_asof(res, dfs[i], on='timestamp', direction='backward')
        if 'receipt_timestamp_x' in res:
            res.insert(1, 'receipt_timestamp', res['receipt_timestamp_x'])
            res = res.drop(columns=['receipt_timestamp_x', 'receipt_timestamp_y'])
    return res


def intervals_almost_equal(i1: Interval, i2: Interval, diff=0.15) -> bool:
    return abs(i1.upper - i2.upper) <= diff and abs(i1.lower - i2.lower) <= diff

