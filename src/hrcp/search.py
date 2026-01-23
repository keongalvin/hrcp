"""Search functions for HRCP trees.

Provides find, filter, exists, and count operations.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

if TYPE_CHECKING:
    from hrcp.core import Resource
    from hrcp.core import ResourceTree


def walk_resource(resource: Resource) -> Iterator[Resource]:
    """Recursively walk a Resource and its children."""
    yield resource
    for child in resource.children.values():
        yield from walk_resource(child)


def matches_criteria(resource: Resource, criteria: dict[str, Any]) -> bool:
    """Check if resource matches all criteria."""
    return all(resource.attributes.get(key) == value for key, value in criteria.items())


def find(
    tree: ResourceTree,
    path: str | None = None,
    **criteria: Any,
) -> list[Resource]:
    """Find resources matching attribute criteria.

    Args:
        tree: The tree to search.
        path: Optional path to restrict search to a subtree.
        **criteria: Attribute key-value pairs to match.

    Returns:
        List of resources where all criteria match.
    """
    start = tree.get(path) if path else tree.root

    if start is None:
        return []

    return [
        resource
        for resource in walk_resource(start)
        if matches_criteria(resource, criteria)
    ]


def find_first(
    tree: ResourceTree,
    path: str | None = None,
    **criteria: Any,
) -> Resource | None:
    """Find first resource matching attribute criteria.

    Args:
        tree: The tree to search.
        path: Optional path to restrict search to a subtree.
        **criteria: Attribute key-value pairs to match.

    Returns:
        First matching resource, or None if not found.
    """
    start = tree.get(path) if path else tree.root

    if start is None:
        return None

    for resource in walk_resource(start):
        if matches_criteria(resource, criteria):
            return resource

    return None


def filter_resources(
    tree: ResourceTree,
    predicate: Callable[[Resource], bool],
    path: str | None = None,
) -> list[Resource]:
    """Filter resources using a predicate function.

    Args:
        tree: The tree to search.
        predicate: Function that takes a Resource and returns True to include.
        path: Optional path to restrict search to a subtree.

    Returns:
        List of resources where predicate returns True.
    """
    start = tree.get(path) if path else tree.root

    if start is None:
        return []

    return [resource for resource in walk_resource(start) if predicate(resource)]


def exists(
    tree: ResourceTree,
    path: str | None = None,
    **criteria: Any,
) -> bool:
    """Check if any resource matches the criteria.

    Args:
        tree: The tree to search.
        path: Optional path to restrict search to a subtree.
        **criteria: Attribute key-value pairs to match.

    Returns:
        True if at least one matching resource exists.
    """
    return find_first(tree, path=path, **criteria) is not None


def count(
    tree: ResourceTree,
    path: str | None = None,
    **criteria: Any,
) -> int:
    """Count resources matching the criteria.

    Args:
        tree: The tree to search.
        path: Optional path to restrict search to a subtree.
        **criteria: Attribute key-value pairs to match.

    Returns:
        Number of matching resources.
    """
    return len(find(tree, path=path, **criteria))
