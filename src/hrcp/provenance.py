"""Provenance tracking for HRCP - know where every value comes from.

Provenance provides transparency into configuration resolution by tracking:
- Which resource provided a value (source_path)
- How the value was resolved (propagation mode)
- For merged values, which resource contributed each key
- For aggregated values, all contributing resources
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any

from hrcp.propagation import PropagationMode

if TYPE_CHECKING:
    from hrcp.core import Resource


@dataclass
class Provenance:
    """Records the origin and resolution path of a configuration value.

    Attributes:
        value: The resolved configuration value.
        source_path: The path of the resource that provided the value.
                     For INHERIT/NONE, this is the single source.
                     For AGGREGATE, this is the root of the aggregation.
                     For MERGE, this is the deepest resource.
        mode: The propagation mode used to resolve the value.
        key_sources: For MERGE with dict values, maps each key
                     to the path of the resource that provided it.
                     Uses dot notation for nested keys (e.g., "logging.level").
        contributing_paths: For AGGREGATE/COLLECT_ANCESTORS, lists all resource
                           paths that contributed values.
    """

    value: Any
    source_path: str
    mode: PropagationMode
    key_sources: dict[str, str] = field(default_factory=dict)
    contributing_paths: list[str] = field(default_factory=list)


def get_value(
    resource: Resource,
    key: str,
    mode: PropagationMode,
    default: Any = None,
    *,
    with_provenance: bool = False,
) -> Any | Provenance | None:
    """Get a configuration value with optional provenance information.

    This is the unified API for retrieving values based on propagation mode.

    Args:
        resource: The Resource to get the value for.
        key: The attribute key.
        mode: The propagation mode to use.
        default: Default value if attribute not found (not used for AGGREGATE
                 mode or when with_provenance=True).
        with_provenance: If True, return a Provenance object with source
                        tracking. If False, return just the value.

    Returns:
        If with_provenance=False: The effective value based on propagation mode,
            or the default if not found.
        If with_provenance=True: Provenance object containing the value and
            its origin information, or None if value doesn't exist (except
            for AGGREGATE mode which returns Provenance with empty list).
    """
    if mode == PropagationMode.NONE:
        prov = _provenance_none(resource, key)
    elif mode == PropagationMode.INHERIT:
        prov = _provenance_inherit(resource, key)
    elif mode == PropagationMode.AGGREGATE:
        prov = _provenance_aggregate(resource, key)
    elif mode == PropagationMode.MERGE:
        prov = _provenance_merge(resource, key)
    elif mode == PropagationMode.REQUIRE_PATH:
        prov = _provenance_require_path(resource, key)
    elif mode == PropagationMode.COLLECT_ANCESTORS:
        prov = _provenance_collect_ancestors(resource, key)
    else:
        msg = f"Unknown propagation mode: {mode}"
        raise ValueError(msg)

    if with_provenance:
        return prov

    if prov is None:
        return default
    return prov.value


def _provenance_none(resource: Resource, key: str) -> Provenance | None:
    """Get provenance for NONE mode - local value only."""
    value = resource.attributes.get(key)
    if value is None:
        return None

    return Provenance(
        value=value,
        source_path=resource.path,
        mode=PropagationMode.NONE,
    )


def _provenance_inherit(resource: Resource, key: str) -> Provenance | None:
    """Get provenance for INHERIT mode - inheritance from ancestors."""
    current: Resource | None = resource
    while current is not None:
        value = current.attributes.get(key)
        if value is not None:
            return Provenance(
                value=value,
                source_path=current.path,
                mode=PropagationMode.INHERIT,
            )
        current = current.parent

    return None


def _provenance_aggregate(resource: Resource, key: str) -> Provenance:
    """Get provenance for AGGREGATE mode - aggregation from descendants."""
    values: list[Any] = []
    paths: list[str] = []

    _collect_values_with_paths(resource, key, values, paths)

    return Provenance(
        value=values,
        source_path=resource.path,
        mode=PropagationMode.AGGREGATE,
        contributing_paths=paths,
    )


def _provenance_require_path(resource: Resource, key: str) -> Provenance | None:
    """Get provenance for REQUIRE_PATH mode - all ancestors must have truthy value.

    Returns the local value only if ALL nodes from self to root have the
    attribute set to a truthy value. Otherwise returns None.
    """
    # First check if local value exists and is truthy
    local_value = resource.attributes.get(key)
    if not local_value:
        return None

    # Walk up to root, checking each ancestor
    paths: list[str] = [resource.path]
    current: Resource | None = resource.parent
    while current is not None:
        value = current.attributes.get(key)
        if not value:
            return None
        paths.append(current.path)
        current = current.parent

    # All ancestors have truthy values
    return Provenance(
        value=local_value,
        source_path=resource.path,
        mode=PropagationMode.REQUIRE_PATH,
        contributing_paths=list(reversed(paths)),  # Root to leaf order
    )


def _provenance_collect_ancestors(resource: Resource, key: str) -> Provenance:
    """Get provenance for COLLECT_ANCESTORS mode - collect values from self to root.

    Returns a list of all values found from the resource up to the root.
    Useful for custom AND/OR logic across the ancestor path.
    """
    values: list[Any] = []
    paths: list[str] = []

    current: Resource | None = resource
    while current is not None:
        value = current.attributes.get(key)
        if value is not None:
            values.append(value)
            paths.append(current.path)
        current = current.parent

    return Provenance(
        value=values,
        source_path=resource.path,
        mode=PropagationMode.COLLECT_ANCESTORS,
        contributing_paths=paths,
    )


def _collect_values_with_paths(
    resource: Resource,
    key: str,
    values: list[Any],
    paths: list[str],
) -> None:
    """Recursively collect values and their source paths."""
    value = resource.attributes.get(key)
    if value is not None:
        values.append(value)
        paths.append(resource.path)

    for child in resource.children.values():
        _collect_values_with_paths(child, key, values, paths)


def _provenance_merge(resource: Resource, key: str) -> Provenance | None:
    """Get provenance for MERGE mode - deep merge with key tracking."""
    # Collect all values and their sources from root to leaf
    chain: list[tuple[Any, str]] = []  # (value, path)
    current: Resource | None = resource
    while current is not None:
        value = current.attributes.get(key)
        if value is not None:
            chain.append((value, current.path))
        current = current.parent

    if not chain:
        return None

    # Reverse to go from root to leaf
    chain.reverse()

    # Check if we're dealing with dicts
    all_dicts = all(isinstance(v, dict) for v, _ in chain)

    if not all_dicts:
        # Non-dict: use INHERIT behavior (last value wins)
        value, path = chain[-1]
        return Provenance(
            value=value,
            source_path=path,
            mode=PropagationMode.MERGE,
        )

    # Deep merge with key tracking
    result: dict[str, Any] = {}
    key_sources: dict[str, str] = {}

    for d, path in chain:
        _deep_merge_with_tracking(result, d, path, key_sources, prefix="")

    return Provenance(
        value=result,
        source_path=resource.path,
        mode=PropagationMode.MERGE,
        key_sources=key_sources,
    )


def _deep_merge_with_tracking(
    base: dict[str, Any],
    override: dict[str, Any],
    source_path: str,
    key_sources: dict[str, str],
    prefix: str,
) -> None:
    """Recursively merge override into base, tracking key sources.

    Args:
        base: The base dict to merge into.
        override: The dict to merge from.
        source_path: Path of the resource providing override values.
        key_sources: Dict to record which path each key came from.
        prefix: Dot-notation prefix for nested keys.
    """
    for k, v in override.items():
        full_key = f"{prefix}.{k}" if prefix else k

        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            # Recursively merge nested dicts
            _deep_merge_with_tracking(base[k], v, source_path, key_sources, full_key)
        else:
            # Override the value and record source
            base[k] = v
            if isinstance(v, dict):
                # Record all leaf keys in the nested dict
                _record_all_leaf_keys(v, source_path, key_sources, full_key)
            else:
                key_sources[full_key] = source_path


def _record_all_leaf_keys(
    d: dict[str, Any],
    source_path: str,
    key_sources: dict[str, str],
    prefix: str,
) -> None:
    """Record all leaf keys in a dict with their source path."""
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            _record_all_leaf_keys(v, source_path, key_sources, full_key)
        else:
            key_sources[full_key] = source_path
