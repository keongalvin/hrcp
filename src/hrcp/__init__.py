"""HRCP - Hierarchical Resource Configuration with Provenance.

A Python library for managing hierarchical configuration with:
- Inheritance: Config values propagate DOWN from ancestors
- Aggregation: Values aggregate UP from descendants
- Merge: Deep merge of dicts through hierarchy
- Provenance: Track where every value came from
- Schema validation: Enforce constraints on attribute values
- Wildcards: Query across hierarchy with patterns (* and **)
"""

from hrcp.core import Resource
from hrcp.core import ResourceTree
from hrcp.path import basename
from hrcp.path import join_path
from hrcp.path import normalize_path
from hrcp.path import parent_path
from hrcp.path import split_path
from hrcp.propagation import PropagationMode
from hrcp.propagation import get_effective_value
from hrcp.provenance import Provenance
from hrcp.provenance import get_value_with_provenance
from hrcp.schema import PropertySchema
from hrcp.schema import SchemaRegistry
from hrcp.schema import ValidationError
from hrcp.schema import validate_value
from hrcp.wildcards import match_pattern

__all__ = [
    "PropagationMode",
    "PropertySchema",
    "Provenance",
    "Resource",
    "ResourceTree",
    "SchemaRegistry",
    "ValidationError",
    "basename",
    "get_effective_value",
    "get_value_with_provenance",
    "join_path",
    "match_pattern",
    "normalize_path",
    "parent_path",
    "split_path",
    "validate_value",
]
