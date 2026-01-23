"""Propagation modes for HRCP - how values flow through the hierarchy.

HRCP supports four propagation modes:
- NONE: No inheritance, only local values
- DOWN: Values inherit from ancestors (parent to child)
- UP: Values aggregate from descendants (children to parent)
- MERGE_DOWN: Deep merge of dict values from ancestors
"""

from __future__ import annotations

from enum import Enum
from enum import auto


class PropagationMode(Enum):
    """Defines how attribute values propagate through the resource hierarchy.

    Attributes:
        NONE: No propagation - only the resource's own value is used.
        DOWN: Inheritance - values propagate from ancestors to descendants.
               The closest ancestor with the value wins.
        UP: Aggregation - values are collected from all descendants.
            Returns a list of all values found in the subtree.
        MERGE_DOWN: Deep merge - dict values are recursively merged from
                    ancestors, with descendant values taking precedence.
    """

    NONE = auto()
    DOWN = auto()
    UP = auto()
    MERGE_DOWN = auto()
