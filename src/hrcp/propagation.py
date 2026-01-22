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
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from hrcp.core import Resource


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


def get_effective_value(
    resource: Resource,
    key: str,
    mode: PropagationMode,
    default: Any = None,
) -> Any:
    """Get the effective value of an attribute based on propagation mode.

    Args:
        resource: The Resource to get the value for.
        key: The attribute key.
        mode: The propagation mode to use.
        default: Default value if attribute not found (not used for UP mode).

    Returns:
        The effective value based on the propagation mode:
        - NONE: Local value or default
        - DOWN: Inherited value or default
        - UP: List of all values in subtree (empty list if none)
        - MERGE_DOWN: Merged dict or inherited value or default
    """
    if mode == PropagationMode.NONE:
        return _get_none(resource, key, default)
    if mode == PropagationMode.DOWN:
        return _get_down(resource, key, default)
    if mode == PropagationMode.UP:
        return _get_up(resource, key)
    if mode == PropagationMode.MERGE_DOWN:
        return _get_merge_down(resource, key, default)
    msg = f"Unknown propagation mode: {mode}"
    raise ValueError(msg)


def _get_none(resource: Resource, key: str, default: Any) -> Any:
    """Get only the local value, ignoring ancestors."""
    return resource.get_attribute(key, default)


def _get_down(resource: Resource, key: str, default: Any) -> Any:
    """Get value with inheritance from ancestors.

    Walks up the tree until a value is found, returning the first match.
    """
    current: Resource | None = resource
    while current is not None:
        value = current.attributes.get(key)
        if value is not None:
            return value
        current = current.parent
    return default


def _get_up(resource: Resource, key: str) -> list[Any]:
    """Aggregate values from all descendants.

    Returns a list of all values found in the subtree rooted at this resource.
    """
    values: list[Any] = []
    _collect_values(resource, key, values)
    return values


def _collect_values(resource: Resource, key: str, values: list[Any]) -> None:
    """Recursively collect values from a resource and its descendants."""
    value = resource.attributes.get(key)
    if value is not None:
        values.append(value)

    for child in resource.children.values():
        _collect_values(child, key, values)


def _get_merge_down(resource: Resource, key: str, default: Any) -> Any:
    """Get value with deep merge from ancestors.

    For dict values, recursively merges from root to leaf, with descendant
    values taking precedence. For non-dict values, behaves like DOWN.
    """
    # Collect all values from root to this resource
    chain: list[Any] = []
    current: Resource | None = resource
    while current is not None:
        value = current.attributes.get(key)
        if value is not None:
            chain.append(value)
        current = current.parent

    if not chain:
        return default

    # Reverse so we go from root to leaf
    chain.reverse()

    # Check if we're dealing with dicts
    if not all(isinstance(v, dict) for v in chain):
        # If any non-dict, fall back to DOWN behavior (last in chain = leaf)
        return chain[-1]

    # Deep merge all dicts
    result: dict[str, Any] = {}
    for d in chain:
        _deep_merge(result, d)
    return result


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Recursively merge override into base, modifying base in place.

    For nested dicts, recursively merges. For other values, override wins.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
