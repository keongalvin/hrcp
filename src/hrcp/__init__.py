"""HRCP - Hierarchical Resource Configuration with Provenance.

A Python library for managing hierarchical configuration with:
- INHERIT: Config values propagate from ancestors to descendants
- AGGREGATE: Values are collected from descendants
- MERGE: Deep merge of dicts through hierarchy
- REQUIRE_PATH: All ancestors must have truthy values
- COLLECT_ANCESTORS: Collect all values from self to root
- Provenance: Track where every value came from
"""

from importlib.metadata import version

from hrcp.core import Resource
from hrcp.core import ResourceTree
from hrcp.propagation import PropagationMode
from hrcp.provenance import Provenance
from hrcp.provenance import get_value

__version__ = version("hrcp")

__all__ = [
    "PropagationMode",
    "Provenance",
    "Resource",
    "ResourceTree",
    "__version__",
    "get_value",
]
