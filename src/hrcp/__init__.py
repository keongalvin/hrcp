"""HRCP - Hierarchical Resource Configuration with Provenance.

A Python library for managing hierarchical configuration with:
- Inheritance: Config values propagate DOWN from ancestors
- Aggregation: Values aggregate UP from descendants
- Merge: Deep merge of dicts through hierarchy
- Provenance: Track where every value came from
"""

from hrcp.core import ResourceTree
from hrcp.propagation import PropagationMode
from hrcp.provenance import Provenance
from hrcp.provenance import get_value

__all__ = [
    "PropagationMode",
    "Provenance",
    "ResourceTree",
    "get_value",
]
