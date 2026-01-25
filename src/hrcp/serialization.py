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
    """Recursively load children from dict data.

    Args:
        tree: The ResourceTree being populated.
        parent: The parent Resource to add children to.
        children_data: Dictionary mapping child keys to child data dicts.

    Raises:
        TypeError: If child data is not a dict, or child attributes/children
                   have wrong types.
        KeyError: If child is missing required 'name' key.
        ValueError: If child name is empty or contains '/'.
    """
    from hrcp.core import Resource

    for key, child_data in children_data.items():
        if not isinstance(child_data, dict):
            msg = f"child data for '{key}' must be a dict, got {type(child_data).__name__}"
            raise TypeError(msg)

        name = child_data["name"]
        if not isinstance(name, str):
            msg = f"child name must be a string, got {type(name).__name__}"
            raise TypeError(msg)

        attributes = child_data.get("attributes")
        if attributes is not None and not isinstance(attributes, dict):
            msg = f"child attributes must be a dict, got {type(attributes).__name__}"
            raise TypeError(msg)

        nested_children = child_data.get("children", {})
        if not isinstance(nested_children, dict):
            msg = f"child children must be a dict, got {type(nested_children).__name__}"
            raise TypeError(msg)

        child = Resource(
            name=name,
            attributes=attributes,
        )
        parent.add_child(child)
        load_children(tree, child, nested_children)


def tree_from_dict(data: dict[str, Any]) -> ResourceTree:
    """Create a ResourceTree from a dictionary.

    Args:
        data: Dictionary with 'name' (required), 'attributes' (optional dict),
              and 'children' (optional dict of child dicts).

    Returns:
        A new ResourceTree populated from the dictionary.

    Raises:
        KeyError: If required 'name' key is missing.
        TypeError: If name is not a string, attributes is not a dict,
                   or children is not a dict.
        ValueError: If name is empty or contains '/'.
    """
    from hrcp.core import ResourceTree

    name = data["name"]
    if not isinstance(name, str):
        msg = f"name must be a string, got {type(name).__name__}"
        raise TypeError(msg)

    attributes = data.get("attributes", {})
    if not isinstance(attributes, dict):
        msg = f"attributes must be a dict, got {type(attributes).__name__}"
        raise TypeError(msg)

    children = data.get("children", {})
    if not isinstance(children, dict):
        msg = f"children must be a dict, got {type(children).__name__}"
        raise TypeError(msg)

    tree = ResourceTree(root_name=name)
    # Set root attributes
    for key, value in attributes.items():
        tree._root._attributes[key] = value  # Bypass validation for load
    # Recursively create children
    load_children(tree, tree._root, children)
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
