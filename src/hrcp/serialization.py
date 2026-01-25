"""Serialization functions for HRCP trees.

Provides conversion to/from dict and JSON formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from hrcp.core import Resource
    from hrcp.core import ResourceTree


def resource_to_dict(resource: Resource) -> dict[str, Any]:
    """Recursively serialize a Resource to a dict."""
    return {
        "name": resource.name,
        "attributes": dict(resource.attributes),
        "children": {
            name: resource_to_dict(child) for name, child in resource.children.items()
        },
    }


def tree_to_dict(tree: ResourceTree) -> dict[str, Any]:
    """Serialize a tree to a dictionary."""
    return resource_to_dict(tree.root)


def load_children(
    tree: ResourceTree,
    parent: Resource,
    children_data: dict[str, dict[str, Any]],
) -> None:
    """Recursively load children from dict data."""
    from hrcp.core import Resource

    for child_data in children_data.values():
        child = Resource(
            name=child_data["name"],
            attributes=child_data.get("attributes"),
        )
        parent.add_child(child)
        load_children(tree, child, child_data.get("children", {}))


def tree_from_dict(data: dict[str, Any]) -> ResourceTree:
    """Create a ResourceTree from a dictionary."""
    from hrcp.core import ResourceTree

    tree = ResourceTree(root_name=data["name"])
    # Set root attributes
    for key, value in data.get("attributes", {}).items():
        tree._root._attributes[key] = value  # Bypass validation for load
    # Recursively create children
    load_children(tree, tree._root, data.get("children", {}))
    return tree


def tree_to_json(tree: ResourceTree, path: str, indent: int = 2) -> None:
    """Save a tree to a JSON file."""
    import json
    from pathlib import Path

    data = tree_to_dict(tree)
    with Path(path).open("w") as f:
        json.dump(data, f, indent=indent)


def tree_from_json(path: str) -> ResourceTree:
    """Load a ResourceTree from a JSON file."""
    import json
    from pathlib import Path

    with Path(path).open() as f:
        data = json.load(f)
    return tree_from_dict(data)
