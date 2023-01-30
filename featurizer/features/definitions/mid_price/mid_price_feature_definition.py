from typing import List, Type, Union, Dict
from streamz import Stream
from featurizer.features.definitions.feature_definition import FeatureDefinition
from featurizer.features.data.data_definition import DataDefinition, Event, EventSchema
from featurizer.features.feature_tree.feature_tree import FeatureTreeNode
from featurizer.features.definitions.l2_book_snapshot.l2_book_snapshot_feature_definition import L2BookSnapshotFeatureDefinition
from featurizer.features.blocks.blocks import BlockMeta
from featurizer.features.blocks.utils import identity_grouping
from portion import IntervalDict
import toolz


class MidPriceFeatureDefinition(FeatureDefinition):

    @classmethod
    def event_schema(cls) -> EventSchema:
        return {
            'timestamp': float,
            'receipt_timestamp': float,
            'mid_price': float
        }

    @classmethod
    def stream(cls, upstreams: Dict[FeatureTreeNode, Stream], feature_params: Dict) -> Stream:
        l2_book_snapshots_upstream = toolz.first(upstreams.values())
        return l2_book_snapshots_upstream.map(
            lambda snap: cls.construct_event(
                snap['timestamp'],
                snap['receipt_timestamp'],
                (snap['bids'][0][0] + snap['asks'][0][0]) / 2,
            )
        )

    @classmethod
    def dep_upstream_schema(cls) -> List[Type[DataDefinition]]:
        return [L2BookSnapshotFeatureDefinition]

    @classmethod
    def group_dep_ranges(cls, ranges: List[BlockMeta], feature: FeatureTreeNode, dep_feature: FeatureTreeNode) -> IntervalDict:  # TODO typehint Block/BlockRange/BlockMeta/BlockRangeMeta
        return identity_grouping(ranges)
