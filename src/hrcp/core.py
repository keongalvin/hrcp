"""Core classes for HRCP - Hierarchical Resource Configuration with Provenance."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING
from typing import Any

from hrcp.schema import SchemaRegistry

if TYPE_CHECKING:
    pass


class Resource:
    """A node in the HRCP configuration tree.

    Each Resource represents a single configurable entity with:
    - A unique name within its parent's children
    - A dictionary of configuration attributes
    - Optional parent reference (None for root)
    - Dictionary of child Resources

    Example:
        >>> root = Resource(name="region", attributes={"provider": "aws"})
        >>> dc = Resource(name="us-east-1")
        >>> root.add_child(dc)
        >>> dc.path
        '/region/us-east-1'
    """

    def __init__(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        schema_registry: SchemaRegistry | None = None,
    ) -> None:
        """Create a new Resource.

        Args:
            name: Unique identifier for this resource within its parent.
                  Cannot be empty or contain '/'.
            attributes: Initial configuration key-value pairs.
            schema_registry: Optional registry for attribute validation.

        Raises:
            ValueError: If name is empty or contains '/'.
            ValidationError: If initial attributes fail validation.
        """
        if not name:
            msg = "name cannot be empty"
            raise ValueError(msg)
        if "/" in name:
            msg = "name cannot contain '/'"
            raise ValueError(msg)

        self._name = name
        self._schema_registry = schema_registry
        self._parent: Resource | None = None
        self._children: dict[str, Resource] = {}

        # Initialize attributes with validation
        self._attributes: dict[str, Any] = {}
        if attributes:
            for key, value in attributes.items():
                self.set_attribute(key, value)

    @property
    def name(self) -> str:
        """The resource's name (unique within parent)."""
        return self._name

    @property
    def attributes(self) -> dict[str, Any]:
        """The resource's configuration attributes."""
        return self._attributes

    @property
    def parent(self) -> Resource | None:
        """The parent Resource, or None if this is a root."""
        return self._parent

    @property
    def children(self) -> dict[str, Resource]:
        """Dictionary of child Resources keyed by name."""
        return self._children

    @property
    def path(self) -> str:
        """The full path from root to this Resource.

        Returns:
            Path string like '/region/datacenter/host'.
        """
        if self._parent is None:
            return f"/{self._name}"
        return f"{self._parent.path}/{self._name}"

    def add_child(self, child: Resource) -> None:
        """Add a child Resource.

        Args:
            child: The Resource to add as a child.

        Raises:
            ValueError: If a child with the same name already exists.
        """
        if child.name in self._children:
            msg = f"Child '{child.name}' already exists"
            raise ValueError(msg)

        self._children[child.name] = child
        child._parent = self

    def remove_child(self, name: str) -> Resource:
        """Remove and return a child Resource by name.

        Args:
            name: The name of the child to remove.

        Returns:
            The removed Resource.

        Raises:
            KeyError: If no child with that name exists.
        """
        child = self._children.pop(name)
        child._parent = None
        return child

    def get_child(self, name: str) -> Resource | None:
        """Get a child Resource by name.

        Args:
            name: The name of the child to retrieve.

        Returns:
            The child Resource, or None if not found.
        """
        return self._children.get(name)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute value.

        Args:
            key: The attribute name.
            value: The attribute value.

        Raises:
            ValidationError: If the value fails schema validation.
        """
        if self._schema_registry is not None:
            self._schema_registry.validate(key, value, self.path)
        self._attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get an attribute value.

        Args:
            key: The attribute name.
            default: Value to return if attribute doesn't exist.

        Returns:
            The attribute value, or default if not found.
        """
        return self._attributes.get(key, default)

    def delete_attribute(self, key: str) -> None:
        """Delete an attribute.

        Args:
            key: The attribute name to delete.

        Raises:
            KeyError: If the attribute doesn't exist.
        """
        del self._attributes[key]

    def __repr__(self) -> str:
        """Return a string representation of the Resource."""
        return f"Resource(name={self._name!r}, path={self.path!r})"


class ResourceTree:
    """Container and manager for an HRCP resource hierarchy.

    The ResourceTree provides a convenient interface for working with
    a tree of Resources, including path-based access, creation, and
    traversal operations.

    Example:
        >>> tree = ResourceTree(root_name="infrastructure")
        >>> tree.create("/infrastructure/us-east/dc1", attributes={"region": "us-east-1"})
        >>> host = tree.get("/infrastructure/us-east/dc1")
        >>> host.attributes
        {'region': 'us-east-1'}
    """

    def __init__(self, root_name: str = "root") -> None:
        """Create a new ResourceTree.

        Args:
            root_name: Name for the root Resource.
        """
        self._schema_registry = SchemaRegistry()
        self._root = Resource(name=root_name, schema_registry=self._schema_registry)

    def define(self, key: str, **kwargs: Any) -> None:
        """Define a schema for an attribute.

        Args:
            key: The attribute key.
            **kwargs: Schema constraints (type_, choices, ge, le, validator).
        """
        self._schema_registry.define(key, **kwargs)

    @property
    def schema(self) -> SchemaRegistry:
        """The schema registry for this tree.

        Allows introspection of defined schemas:
            for key, schema in tree.schema.items():
                print(f"{key}: {schema.type_}")
        """
        return self._schema_registry

    def to_json_schema(self) -> dict[str, Any]:
        """Export the tree's schema as JSON Schema.

        Returns:
            A dict conforming to JSON Schema draft 2020-12.
        """
        return self._schema_registry.to_json_schema()

    def get_attribute_or_default(self, path: str, key: str) -> Any | None:
        """Get an attribute value, falling back to schema default if not set.

        Args:
            path: Path to the resource.
            key: Attribute key to retrieve.

        Returns:
            The attribute value if set, otherwise the schema default,
            or None if neither exists.

        Raises:
            KeyError: If the path does not exist.
        """
        resource = self.get(path)
        if resource is None:
            msg = f"Path not found: {path}"
            raise KeyError(msg)

        value = resource.attributes.get(key)
        if value is not None:
            return value

        return self._schema_registry.get_default(key)

    def get_missing_required(self, path: str) -> list[str]:
        """Get list of missing required attributes at a path.

        Args:
            path: Path to the resource.

        Returns:
            List of required attribute keys that are not set.

        Raises:
            KeyError: If the path does not exist.
        """
        resource = self.get(path)
        if resource is None:
            msg = f"Path not found: {path}"
            raise KeyError(msg)

        return [
            key
            for key in self._schema_registry.required_fields()
            if key not in resource.attributes
        ]

    def validate_required(self, path: str) -> None:
        """Validate that all required attributes are present at a path.

        Args:
            path: Path to the resource.

        Raises:
            KeyError: If the path does not exist.
            ValidationError: If any required attribute is missing.
        """
        from hrcp.schema import ValidationError

        missing = self.get_missing_required(path)
        if missing:
            msg = f"Missing required attributes at {path}: {', '.join(missing)}"
            raise ValidationError(msg)

    @property
    def root(self) -> Resource:
        """The root Resource of the tree."""
        return self._root

    def get(self, path: str) -> Resource | None:
        """Get a Resource by its path.

        Args:
            path: The path to the Resource (e.g., '/root/child/grandchild').
                  Use '/' to get the root.

        Returns:
            The Resource at the path, or None if not found.
        """
        if path == "/":
            return self._root

        # Remove leading slash and split
        parts = path.lstrip("/").split("/")

        # First part should match root name
        if not parts or parts[0] != self._root.name:
            return None

        # Traverse from root
        current = self._root
        for part in parts[1:]:
            child = current.get_child(part)
            if child is None:
                return None
            current = child

        return current

    def create(
        self,
        path: str,
        attributes: dict[str, Any] | None = None,
    ) -> Resource:
        """Create a Resource at the specified path.

        Creates any intermediate Resources needed to build the path.

        Args:
            path: The path where the Resource should be created.
            attributes: Initial attributes for the new Resource.

        Returns:
            The newly created Resource.

        Raises:
            ValueError: If path doesn't start with root name or
                       if Resource already exists at path.
        """
        parts = path.lstrip("/").split("/")

        # Validate path starts with root
        if not parts or parts[0] != self._root.name:
            msg = f"Path must start with '/{self._root.name}'"
            raise ValueError(msg)

        # Check if target already exists
        if self.get(path) is not None:
            msg = f"Resource already exists at '{path}'"
            raise ValueError(msg)

        # Traverse/create path
        current = self._root
        for i, part in enumerate(parts[1:], start=1):
            child = current.get_child(part)
            if child is None:
                # Create intermediate or final resource
                is_final = i == len(parts) - 1
                child = Resource(
                    name=part,
                    attributes=attributes if is_final else None,
                    schema_registry=self._schema_registry,
                )
                current.add_child(child)
            current = child

        return current

    def delete(self, path: str) -> Resource:
        """Delete a Resource and its subtree.

        Args:
            path: The path to the Resource to delete.

        Returns:
            The deleted Resource.

        Raises:
            ValueError: If attempting to delete the root.
            KeyError: If no Resource exists at the path.
        """
        parts = path.lstrip("/").split("/")

        # Check if trying to delete root
        if len(parts) == 1 and parts[0] == self._root.name:
            msg = "cannot delete root"
            raise ValueError(msg)

        # Find the resource and its parent
        resource = self.get(path)
        if resource is None:
            msg = f"No resource at '{path}'"
            raise KeyError(msg)

        # Remove from parent
        parent = resource.parent
        if parent is not None:
            return parent.remove_child(resource.name)

        msg = f"No resource at '{path}'"
        raise KeyError(msg)

    def walk(self, start_path: str = "/") -> Iterator[Resource]:
        """Iterate over all Resources in the tree (depth-first).

        Args:
            start_path: Path to start walking from (default: root).

        Yields:
            Each Resource in depth-first order.

        Raises:
            KeyError: If start_path doesn't exist.
        """
        if start_path == "/":
            start: Resource = self._root
        else:
            maybe_start = self.get(start_path)
            if maybe_start is None:
                msg = f"No resource at '{start_path}'"
                raise KeyError(msg)
            start = maybe_start

        yield from self._walk_resource(start)

    def _walk_resource(self, resource: Resource) -> Iterator[Resource]:
        """Recursively walk a Resource and its children."""
        yield resource
        for child in resource.children.values():
            yield from self._walk_resource(child)

    def __len__(self) -> int:
        """Return the total number of Resources in the tree."""
        return sum(1 for _ in self.walk())

    def query(self, pattern: str) -> list[Resource]:
        """Query resources matching a wildcard pattern.

        Supports:
        - Single wildcard (*): matches any single path segment
        - Double wildcard (**): matches any number of segments (including zero)

        Args:
            pattern: Path pattern like '/root/*/child' or '/root/**/leaf'

        Returns:
            List of matching Resources.
        """
        from hrcp.wildcards import match_pattern

        return [
            resource
            for resource in self.walk()
            if match_pattern(resource.path, pattern)
        ]

    def query_values(
        self,
        pattern: str,
        key: str,
        mode: Any,  # PropagationMode
    ) -> list[Any]:
        """Get attribute values from resources matching a pattern.

        Args:
            pattern: Path pattern for matching resources.
            key: The attribute key to retrieve.
            mode: Propagation mode for value resolution.

        Returns:
            List of values from matching resources (excludes None values).
        """
        from hrcp.propagation import PropagationMode
        from hrcp.provenance import get_value

        results: list[Any] = []
        for resource in self.query(pattern):
            value = get_value(resource, key, mode)
            if mode == PropagationMode.UP:
                # UP returns a list, extend if not empty
                if value:
                    results.extend(value)
            elif value is not None:
                results.append(value)
        return results

    def to_dict(self) -> dict[str, Any]:
        """Serialize the tree to a dictionary.

        Returns:
            A dict representation of the tree that can be serialized to JSON.
        """
        from hrcp.serialization import tree_to_dict

        return tree_to_dict(self)

    def _resource_to_dict(self, resource: Resource) -> dict[str, Any]:
        """Recursively serialize a Resource to a dict."""
        from hrcp.serialization import resource_to_dict

        return resource_to_dict(resource)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceTree:
        """Create a ResourceTree from a dictionary.

        Args:
            data: A dict representation of the tree.

        Returns:
            A new ResourceTree with the data.
        """
        from hrcp.serialization import tree_from_dict

        return tree_from_dict(data)

    @classmethod
    def _load_children(
        cls,
        tree: ResourceTree,
        parent: Resource,
        children_data: dict[str, dict[str, Any]],
    ) -> None:
        """Recursively load children from dict data."""
        from hrcp.serialization import load_children

        load_children(tree, parent, children_data)

    def to_json(self, path: str, indent: int = 2) -> None:
        """Save the tree to a JSON file.

        Args:
            path: Path to the output JSON file.
            indent: Indentation level for human-readable output.
        """
        from hrcp.serialization import tree_to_json

        tree_to_json(self, path, indent)

    @classmethod
    def from_json(cls, path: str) -> ResourceTree:
        """Load a ResourceTree from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            A new ResourceTree loaded from the file.
        """
        from hrcp.serialization import tree_from_json

        return tree_from_json(path)

    def to_yaml(self, path: str | None = None) -> str:
        """Serialize the tree to a YAML string.

        Args:
            path: Optional file path to write to. If None, returns string.

        Returns:
            A YAML string representation of the tree.
        """
        from hrcp.serialization import tree_to_yaml

        return tree_to_yaml(self, path)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> ResourceTree:
        """Create a ResourceTree from a YAML string.

        Args:
            yaml_str: A YAML string representation of the tree.

        Returns:
            A new ResourceTree with the data.
        """
        from hrcp.serialization import tree_from_yaml

        return tree_from_yaml(yaml_str)

    @classmethod
    def from_yaml_file(cls, path: str) -> ResourceTree:
        """Create a ResourceTree from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            A new ResourceTree loaded from the file.
        """
        from hrcp.serialization import tree_from_yaml_file

        return tree_from_yaml_file(path)

    def to_toml(self, path: str | None = None) -> str:
        """Serialize the tree to a TOML string.

        TOML format uses nested tables for children. Root attributes
        are at top level, children become [table] sections.

        Args:
            path: Optional file path to write to. If None, returns string.

        Returns:
            A TOML string representation of the tree.
        """
        from hrcp.serialization import tree_to_toml

        return tree_to_toml(self, path)

    @classmethod
    def from_toml(cls, toml_str: str, root_name: str = "root") -> ResourceTree:
        """Create a ResourceTree from a TOML string.

        Args:
            toml_str: A TOML string.
            root_name: Name for the root resource.

        Returns:
            A new ResourceTree with the data.
        """
        from hrcp.serialization import tree_from_toml

        return tree_from_toml(toml_str, root_name)

    @classmethod
    def from_toml_file(cls, path: str, root_name: str = "root") -> ResourceTree:
        """Create a ResourceTree from a TOML file.

        Args:
            path: Path to the TOML file.
            root_name: Name for the root resource.

        Returns:
            A new ResourceTree loaded from the file.
        """
        from hrcp.serialization import tree_from_toml_file

        return tree_from_toml_file(path, root_name)

    def validate_all(self, path: str | None = None) -> dict[str, list[str]]:
        """Validate all resources against schema requirements.

        Args:
            path: Optional path to restrict validation to a subtree.

        Returns:
            Dict mapping resource paths to lists of missing required fields.
            Empty dict means all resources are valid.
        """
        errors: dict[str, list[str]] = {}
        start = self.get(path) if path else self.root

        if start is None:
            return errors

        required = self._schema_registry.required_fields()

        for resource in self._walk_resource(start):
            missing = [key for key in required if key not in resource.attributes]
            if missing:
                errors[resource.path] = missing

        return errors

    def is_valid(self, path: str | None = None) -> bool:
        """Check if all resources pass validation.

        Args:
            path: Optional path to restrict check to a subtree.

        Returns:
            True if no validation errors, False otherwise.
        """
        return len(self.validate_all(path)) == 0

    def validation_summary(self, path: str | None = None) -> str:
        """Get human-readable validation report.

        Args:
            path: Optional path to restrict report to a subtree.

        Returns:
            Multi-line string summarizing validation errors.
        """
        errors = self.validate_all(path)

        if not errors:
            return "All resources are valid."

        lines = ["Validation Errors:", ""]

        for resource_path, missing_keys in sorted(errors.items()):
            lines.append(f"{resource_path}:")
            for key in missing_keys:
                schema = self._schema_registry.get(key)
                desc = ""
                if schema and schema.description:
                    desc = f" - {schema.description}"
                lines.append(f"  - Missing required: {key}{desc}")
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return a string representation of the ResourceTree."""
        return f"ResourceTree(root={self._root.name!r}, size={len(self)})"
