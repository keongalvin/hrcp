"""Propagation modes for HRCP - how values flow through the hierarchy.

HRCP supports six propagation modes:
- NONE: No inheritance, only local values
- INHERIT: Values inherit from ancestors (parent to child)
- AGGREGATE: Values aggregate from descendants (children to parent)
- MERGE: Deep merge of dict values from ancestors
- REQUIRE_PATH: Value returned only if ALL ancestors have truthy values
- COLLECT_ANCESTORS: Collect all values from self to root into a list
"""

from __future__ import annotations

from enum import Enum
from enum import auto


class PropagationMode(Enum):
    """Defines how attribute values propagate through the resource hierarchy.

    Attributes:
        NONE: No propagation - only the resource's own value is used.
        INHERIT: Inheritance - values propagate from ancestors to descendants.
                 The closest ancestor with the value wins.
        AGGREGATE: Aggregation - values are collected from all descendants.
                   Returns a list of all values found in the subtree.
        MERGE: Deep merge - dict values are recursively merged from
               ancestors, with descendant values taking precedence.
        REQUIRE_PATH: All ancestors (including self) must have a truthy value.
                      Returns the local value if ALL nodes from self to root
                      have the attribute set to a truthy value, else None.
        COLLECT_ANCESTORS: Collect values from self up to root into a list.
                           Useful for custom AND/OR logic across the path.
    """

    NONE = auto()
    INHERIT = auto()
    AGGREGATE = auto()
    MERGE = auto()
    REQUIRE_PATH = auto()
    COLLECT_ANCESTORS = auto()

    # Aliases for backward compatibility (deprecated)
    DOWN = INHERIT
    UP = AGGREGATE
    MERGE_DOWN = MERGE
