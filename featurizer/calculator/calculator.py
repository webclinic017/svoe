import time
from typing import Dict, List, Tuple, Optional

import ray
from ray.dag import DAGNode
from ray.types import ObjectRef

from featurizer.features.feature_tree.feature_tree import Feature, postorder
from featurizer.blocks.blocks import Block, meta_to_interval, interval_to_meta, get_overlaps, BlockRangeMeta, \
    prune_overlaps, range_meta_to_interval, ranges_to_interval_dict, BlockMeta, overlaps_keys
from portion import Interval, IntervalDict
import pandas as pd

from featurizer.calculator.tasks import calculate_feature, load_if_needed, bind_and_cache, context
from utils.pandas.df_utils import concat, sub_df_ts, merge_asof_multi


# TODO re: cache https://discuss.ray.io/t/best-way-to-share-memory-for-ray-tasks/3759
# https://sourcegraph.com/github.com/ray-project/ray@master/-/blob/python/ray/tests/test_object_assign_owner.py?subtree=true


def build_feature_task_graph(
    dag: Dict[Feature, Dict[Interval, Dict[Interval, DAGNode]]], # DAGNodes per feature per range
    feature: Feature,
    data_ranges_meta: Dict[Feature, List[BlockRangeMeta]],
    obj_ref_cache: Dict[str, Dict[Interval, Tuple[int, Optional[ObjectRef]]]],
    features_to_store: Optional[List[Feature]] = None,
    stored_feature_blocks_meta: Optional[Dict[Feature, Dict[Interval, BlockMeta]]] = None,
) -> Dict[Feature, Dict[Interval, Dict[Interval, DAGNode]]]:
    features_ranges_meta = {}

    def tree_traversal_callback(feature: Feature):
        if feature.feature_definition.is_data_source():
            # leafs
            # TODO decouple derived feature_ranges_meta and input data ranges meta
            ranges = data_ranges_meta[feature]  # this is already populated for Data in load_data_ranges above
            for block_range_meta in ranges:
                if feature not in dag:
                    dag[feature] = {}
                range_interval = range_meta_to_interval(block_range_meta)
                nodes = {}
                for block_meta in block_range_meta:
                    interval = meta_to_interval(block_meta)
                    path = block_meta['path']
                    # node = load_if_needed.bind(path, False)
                    ctx = context(feature.feature_key, interval)
                    node = bind_and_cache(load_if_needed, obj_ref_cache, ctx, path=path, is_feature=False)

                    # TODO validate no overlapping intervals here
                    nodes[interval] = node

                # TODO check if duplicate feature/interval
                dag[feature][range_interval] = nodes
            return

        ranges_per_dep_feature = {}
        for dep_feature in feature.children:
            meta = data_ranges_meta[dep_feature] if dep_feature.feature_definition.is_data_source() else features_ranges_meta[dep_feature]
            ranges_per_dep_feature[dep_feature] = ranges_to_interval_dict(meta)

        range_intervals = prune_overlaps(get_overlaps(ranges_per_dep_feature))
        for range_interval in range_intervals:
            range_meta_per_dep_feature = range_intervals[range_interval]

            grouped_ranges_by_dep_feature = {}
            for dep_feature in feature.children:
                dep_ranges = range_meta_per_dep_feature[dep_feature]
                # TODO this should be in Feature class
                grouped_ranges_by_dep_feature[dep_feature] = feature.feature_definition.group_dep_ranges(dep_ranges, feature, dep_feature)

            overlaps = get_overlaps(grouped_ranges_by_dep_feature)
            block_range_meta = []
            nodes = {}
            for interval, overlap in overlaps.items():
                # TODO add size_kb/memory_size_kb to proper size memory usage for aggregate tasks downstream
                result_meta = interval_to_meta(interval)
                block_range_meta.append(result_meta)
                if feature not in dag:
                    dag[feature] = {}

                # TODO use overlap to fetch results of dep delayed funcs
                dep_nodes = {}
                for dep_feature in overlap:
                    ds = []
                    for dep_block_meta in overlap[dep_feature]:
                        dep_interval = meta_to_interval(dep_block_meta)
                        dep_node = dag[dep_feature][range_interval][dep_interval]
                        ds.append(dep_node)
                    dep_nodes[dep_feature] = ds

                ctx = context(feature.feature_key, interval)
                if stored_feature_blocks_meta is not None and feature in stored_feature_blocks_meta and interval in stored_feature_blocks_meta[feature]:
                    path = stored_feature_blocks_meta[feature][interval]['path']
                    # node = load_if_needed.bind(path, True)
                    node = bind_and_cache(load_if_needed, obj_ref_cache, ctx, path=path, is_feature=True)
                else:
                    store = features_to_store is not None and feature in features_to_store
                    # node = calculate_feature.bind(feature, dep_nodes, interval, store)
                    node = bind_and_cache(calculate_feature, obj_ref_cache, ctx, feature=feature, dep_nodes=dep_nodes, interval=interval, store=store)

                # TODO validate interval is withtin range_interval
                nodes[interval] = node

            # TODO check if range_interval intersects with existing keys/intervals"
            dag[feature][range_interval] = nodes
            # TODO check if duplicate feature
            if feature not in features_ranges_meta:
                features_ranges_meta[feature] = [block_range_meta]
            else:
                features_ranges_meta[feature].append(block_range_meta)

    postorder(feature, tree_traversal_callback)

    return dag


def build_feature_set_task_graph(
    features: List[Feature],
    data_ranges_meta: Dict[Feature, List[BlockRangeMeta]],
    obj_ref_cache: Dict[str, Dict[Interval, Tuple[int, Optional[ObjectRef]]]],
    features_to_store: Optional[List[Feature]] = None,
    stored_feature_blocks_meta: Optional[Dict[Feature, Dict[Interval, BlockMeta]]] = None,
) -> Dict[Feature, Dict[Interval, Dict[Interval, DAGNode]]]:
    dag = {}
    for feature in features:
        dag = build_feature_task_graph(
            dag, feature, data_ranges_meta, obj_ref_cache,
            features_to_store=features_to_store,
            stored_feature_blocks_meta=stored_feature_blocks_meta
        )

    return dag


def execute_graph_nodes(nodes: List[DAGNode]) -> List[Block]:
    results_refs = []
    executing_refs = []
    max_concurrent_dags = 12 # num_cpus
    i = 0
    with ray.init(address='auto'):
        # TODO merge this with Scheduler in PipelineRunner
        while i < len(nodes):
            if len(executing_refs) < max_concurrent_dags:
                print(f'Scheduled {i + 1}/{len(nodes)} dags')
                executing_refs.append(nodes[i].execute())
                i += 1
            ready, remaining = ray.wait(executing_refs, num_returns=len(executing_refs), fetch_local=False, timeout=0.001)
            results_refs.extend(ready)
            executing_refs = remaining

        # all scheduled, wait for completion
        while len(executing_refs) > 0:
            ready, remaining = ray.wait(executing_refs, num_returns=len(executing_refs), fetch_local=False, timeout=30)
            results_refs.extend(ready)
            executing_refs = remaining

        return ray.get(results_refs)


def point_in_time_join_dag(
    dag: Dict[Feature, Dict[Interval, Dict[Interval, DAGNode]]],
    features_to_join: List[Feature],
    label_feature: Feature
) -> Dict[Interval, Dict[Interval, DAGNode]]:
    # get range overlaps first
    ranges_per_feature = {}
    for feature in features_to_join:
        if feature not in dag:
            raise ValueError(f'Feature {feature} not found in dag')
        ranges_dict = IntervalDict()
        for range_interval in dag[feature]:
            range_and_node_list = []
            range_dict = dag[feature][range_interval]

            # TODO make sure range_list is ts sorted
            for interval in range_dict:
                range_and_node_list.append((interval, range_dict[interval]))
            if overlaps_keys(range_interval, ranges_dict):
                raise ValueError(f'Overlapping intervals: for {range_interval}')
            ranges_dict[range_interval] = range_and_node_list
        ranges_per_feature[feature] = ranges_dict

    overlapped_range_intervals = prune_overlaps(get_overlaps(ranges_per_feature))

    res = {}

    for range_interval in overlapped_range_intervals:
        nodes_per_feature = overlapped_range_intervals[range_interval]

        nodes_per_feature_per_interval = {}
        for feature in nodes_per_feature:
            nodes_per_interval = IntervalDict()
            for interval_node_tuple in nodes_per_feature[feature]:
                interval = interval_node_tuple[0]
                node = interval_node_tuple[1]
                nodes_per_interval[interval] = node
            nodes_per_feature_per_interval[feature] = nodes_per_interval

        overlaps = get_overlaps(nodes_per_feature_per_interval)

        def get_prev_nodes(cur_nodes_per_feature: Dict[Feature, ObjectRef]) -> Dict[Feature, ObjectRef]:
            res = {}
            for feature in cur_nodes_per_feature:
                # TODO here we assume they are ts sorted
                nodes = list(nodes_per_feature_per_interval[feature].values())
                prev_node = None
                cur_node = cur_nodes_per_feature[feature]
                for i in range(len(nodes)):
                    if nodes[i] == cur_node and i > 0:
                        prev_node = nodes[i - 1]

                if prev_node is not None:
                    res[feature] = prev_node

            return res

        joined_nodes = {}
        for interval in overlaps:
            nodes_per_feature = overlaps[interval]
            # we need to know prev values for join
            # in case one value is at the start of current block and another is in the end of prev block
            prev_interval_nodes = get_prev_nodes(nodes_per_feature)
            # TODO set resource spec here
            join_node = _point_in_time_join_block.bind(interval, nodes_per_feature, prev_interval_nodes, label_feature)
            joined_nodes[interval] = join_node

        res[range_interval] = joined_nodes

    return res


# TODO set memory consumption
@ray.remote
def _point_in_time_join_block(
    interval: Interval,
    blocks_refs_per_feature: Dict[Feature, ObjectRef[Block]],
    prev_block_ref_per_feature: Dict[Feature, ObjectRef[Block]],
    label_feature: Feature,
) -> pd.DataFrame:
    # TODO this loads all dfs at once,
    # TODO can we do it iteratively so gc has time to collect old dfs to reduce mem footprint? (tradeoff speed/memory)
    print('Join started')
    t = time.time()
    concated = {}
    for feature in blocks_refs_per_feature:
        block_refs = [prev_block_ref_per_feature[feature]] if feature in prev_block_ref_per_feature else []
        block_refs.append(blocks_refs_per_feature[feature])

        # TODO have single ray.get
        blocks = ray.get(block_refs)
        concated[feature] = concat(blocks)

    dfs = [concated[label_feature]] # make sure label is first so we use it's ts as join keys
    for feature in concated:
        if feature == label_feature:
            # it's already there
            continue
        dfs.append(concated[feature])

    merged = merge_asof_multi(dfs)

    print(f'Join finished {time.time() - t}s')
    return sub_df_ts(merged, interval.lower, interval.upper)


# TODO type hint
# TODO for feature scaling https://github.com/online-ml/river/blob/main/river/preprocessing/scale.py
# def build_feature_label_set_task_graph(
#     features: List[Feature],
#     ranges_meta: Dict[Feature, List],
#     label: Feature,
#     label_lookahead: Optional[str] = None,
# ):
#     # TODO implement label lookahead
#     dag = {}
#     dag = build_feature_set_task_graph(dag, features, ranges_meta)
#
#     return point_in_time_join_dag(dag, features, label)
