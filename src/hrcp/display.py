"""Display functions for HRCP trees.

Provides pretty printing, depth calculation, and attribute key collection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hrcp.core import Resource
    from hrcp.core import ResourceTree


def resource_depth(resource: Resource) -> int:
    """Calculate depth of subtree rooted at resource."""
    if not resource.children:
        return 1
    return 1 + max(resource_depth(c) for c in resource.children.values())


def tree_depth(tree: ResourceTree) -> int:
    """Get the maximum depth of the tree.

    Returns:
        Maximum depth (1 for root only, 2 for root with children, etc.)
    """
    return resource_depth(tree.root)


def attribute_keys(tree: ResourceTree) -> set[str]:
    """Get all unique attribute keys used in the tree.

    Returns:
        Set of all attribute key names.
    """
    keys: set[str] = set()
    for resource in tree.walk():
        keys.update(resource.attributes.keys())
    return keys


def pretty_resource(
    resource: Resource,
    lines: list[str],
    prefix: str,
    compact: bool,
    is_root: bool = True,
) -> None:
    """Recursively build pretty print lines."""
    # Build the line for this resource
    if compact:
        lines.append(f"{prefix}{resource.name}")
    else:
        attrs_str = ""
        if resource.attributes:
            attrs = ", ".join(
                f"{k}={v!r}" for k, v in sorted(resource.attributes.items())
            )
            attrs_str = f" [{attrs}]"
        lines.append(f"{prefix}{resource.name}{attrs_str}")

    # Process children
    children = list(resource.children.values())
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        if is_root:
            child_prefix = "├── " if not is_last else "└── "
        else:
            child_prefix = prefix.replace("├── ", "│   ").replace("└── ", "    ")
            child_prefix += "├── " if not is_last else "└── "
            child_prefix.replace("├── ", "│   ").replace("└── ", "    ")

        pretty_resource(child, lines, child_prefix, compact, is_root=False)


def pretty(
    tree: ResourceTree, path: str | None = None, *, compact: bool = False
) -> str:
    """Get a pretty-printed string representation of the tree.

    Args:
        tree: The tree to pretty print.
        path: Optional path to restrict to a subtree.
        compact: If True, use compact format without attributes.

    Returns:
        A formatted string representation of the tree.
    """
    start = tree.get(path) if path else tree.root
    if start is None:
        return ""

    lines: list[str] = []
    pretty_resource(start, lines, "", compact)
    return "\n".join(lines)
