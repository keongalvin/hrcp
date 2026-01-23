"""Tree operations for HRCP.

Provides clone, merge, copy, move, and rename operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from hrcp.core import Resource
    from hrcp.core import ResourceTree

from hrcp.serialization import load_children
from hrcp.serialization import resource_to_dict
from hrcp.serialization import tree_from_dict
from hrcp.serialization import tree_to_dict


def clone(tree: ResourceTree) -> ResourceTree:
    """Create a deep copy of a tree.

    Returns a new ResourceTree with the same structure, attributes,
    and schema definitions, but independent of the original.

    Returns:
        A new ResourceTree that is a deep copy of the original.
    """
    data = tree_to_dict(tree)
    cloned = tree_from_dict(data)

    # Copy schema definitions
    for key, schema in tree._schema_registry.items():
        cloned._schema_registry.define(key, schema)

    return cloned


def clone_subtree(tree: ResourceTree, path: str) -> ResourceTree:
    """Clone a subtree rooted at the given path.

    Args:
        tree: The source tree.
        path: Path to the resource to use as root of new tree.

    Returns:
        A new ResourceTree rooted at the specified resource.

    Raises:
        KeyError: If the path does not exist.
    """
    resource = tree.get(path)
    if resource is None:
        msg = f"Path not found: {path}"
        raise KeyError(msg)

    # Serialize just this resource and its descendants
    data = resource_to_dict(resource)
    cloned = tree_from_dict(data)

    # Copy schema definitions
    for key, schema in tree._schema_registry.items():
        cloned._schema_registry.define(key, schema)

    return cloned


def merge_resource(
    tree: ResourceTree,
    target: Resource,
    source: Resource,
) -> None:
    """Recursively merge source resource into target."""
    # Merge attributes
    for key, value in source.attributes.items():
        target.set_attribute(key, value)

    # Merge children
    for name, source_child in source.children.items():
        target_child = target.get_child(name)
        if target_child is None:
            # Clone the source child and add it
            child_data = resource_to_dict(source_child)
            load_children(tree, target, {name: child_data})
        else:
            # Recursively merge
            merge_resource(tree, target_child, source_child)


def merge(target_tree: ResourceTree, source_tree: ResourceTree) -> None:
    """Merge another tree into the target.

    Recursively merges resources from source into target:
    - New resources are added
    - Existing resource attributes are updated from source
    """
    merge_resource(target_tree, target_tree.root, source_tree.root)


def create_from_dict(
    tree: ResourceTree,
    data: dict[str, Any],
    parent: Resource,
) -> Resource:
    """Create resource from dict and attach to parent."""
    from hrcp.core import Resource

    resource = Resource(
        name=data["name"],
        schema_registry=tree._schema_registry,
    )
    for key, value in data.get("attributes", {}).items():
        resource._attributes[key] = value

    parent.add_child(resource)

    # Recursively create children
    for child_data in data.get("children", {}).values():
        create_from_dict(tree, child_data, resource)

    return resource


def copy(tree: ResourceTree, source_path: str, dest_path: str) -> Resource:
    """Copy a resource (and its subtree) to a new path.

    Args:
        tree: The tree containing the resources.
        source_path: Path of resource to copy.
        dest_path: Destination path for the copy.

    Returns:
        The newly created resource.

    Raises:
        KeyError: If source path doesn't exist.
    """
    source = tree.get(source_path)
    if source is None:
        msg = f"Source path not found: {source_path}"
        raise KeyError(msg)

    # Serialize and recreate at new location
    data = resource_to_dict(source)

    # Extract destination parent and new name
    from hrcp.path import basename
    from hrcp.path import parent_path

    dest_parent_path = parent_path(dest_path)
    new_name = basename(dest_path)

    # Update name in data
    data["name"] = new_name

    # Get or create parent
    dest_parent = tree.get(dest_parent_path)
    if dest_parent is None:
        dest_parent = tree.create(dest_parent_path)

    # Create the copy
    return create_from_dict(tree, data, dest_parent)


def move(tree: ResourceTree, source_path: str, dest_path: str) -> Resource:
    """Move a resource (and its subtree) to a new path.

    Args:
        tree: The tree containing the resources.
        source_path: Path of resource to move.
        dest_path: Destination path.

    Returns:
        The moved resource at its new location.

    Raises:
        KeyError: If source path doesn't exist.
    """
    result = copy(tree, source_path, dest_path)
    tree.delete(source_path)
    return result


def rename(tree: ResourceTree, path: str, new_name: str) -> Resource:
    """Rename a resource in place.

    Args:
        tree: The tree containing the resource.
        path: Path to the resource to rename.
        new_name: New name for the resource.

    Returns:
        The renamed resource.

    Raises:
        KeyError: If path doesn't exist.
    """
    resource = tree.get(path)
    if resource is None:
        msg = f"Path not found: {path}"
        raise KeyError(msg)

    parent = resource.parent
    if parent is None:
        msg = "Cannot rename root resource"
        raise ValueError(msg)

    # Remove from parent with old name
    del parent._children[resource.name]

    # Update name and re-add
    resource._name = new_name
    parent._children[new_name] = resource

    return resource
