"""Serialization functions for HRCP trees.

Provides conversion to/from dict, JSON, YAML, and TOML formats.
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


def tree_to_yaml(tree: ResourceTree, path: str | None = None) -> str:
    """Serialize a tree to a YAML string."""
    import yaml

    data = tree_to_dict(tree)
    yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False)

    if path is not None:
        from pathlib import Path

        Path(path).write_text(yaml_str)

    return yaml_str


def tree_from_yaml(yaml_str: str) -> ResourceTree:
    """Create a ResourceTree from a YAML string."""
    import yaml

    data = yaml.safe_load(yaml_str)
    return tree_from_dict(data)


def tree_from_yaml_file(path: str) -> ResourceTree:
    """Create a ResourceTree from a YAML file."""
    from pathlib import Path

    yaml_str = Path(path).read_text()
    return tree_from_yaml(yaml_str)


def resource_to_toml_dict(resource: Resource) -> dict[str, Any]:
    """Convert resource to TOML-compatible dict."""
    result: dict[str, Any] = dict(resource.attributes)

    # Add children as nested dicts
    for name, child in resource.children.items():
        result[name] = resource_to_toml_dict(child)

    return result


def tree_to_toml(tree: ResourceTree, path: str | None = None) -> str:
    """Serialize a tree to a TOML string."""
    import tomli_w

    data = resource_to_toml_dict(tree.root)
    toml_str = tomli_w.dumps(data)

    if path is not None:
        from pathlib import Path

        Path(path).write_text(toml_str)

    return toml_str


def load_toml_child(
    parent: Resource,
    name: str,
    data: dict[str, Any],
) -> None:
    """Recursively load TOML child resources."""
    from hrcp.core import Resource

    child = Resource(name=name)
    parent.add_child(child)

    for key, value in data.items():
        if isinstance(value, dict):
            load_toml_child(child, key, value)
        else:
            child.set_attribute(key, value)


def tree_from_toml(toml_str: str, root_name: str = "root") -> ResourceTree:
    """Create a ResourceTree from a TOML string."""
    import tomllib

    from hrcp.core import ResourceTree

    data = tomllib.loads(toml_str)
    tree = ResourceTree(root_name=root_name)

    for key, value in data.items():
        if isinstance(value, dict):
            load_toml_child(tree.root, key, value)
        else:
            tree.root.set_attribute(key, value)

    return tree


def tree_from_toml_file(path: str, root_name: str = "root") -> ResourceTree:
    """Create a ResourceTree from a TOML file."""
    from pathlib import Path

    toml_str = Path(path).read_text()
    return tree_from_toml(toml_str, root_name)
