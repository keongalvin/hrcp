"""Core classes for HRCP - Hierarchical Resource Configuration with Provenance."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

if TYPE_CHECKING:
    from hrcp.schema import SchemaRegistry


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


from collections.abc import Iterator

from hrcp.schema import SchemaRegistry


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

        missing = []
        for key in self._schema_registry.required_fields():
            if key not in resource.attributes:
                missing.append(key)

        return missing

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

    def clone(self) -> ResourceTree:
        """Create a deep copy of this tree.

        Returns a new ResourceTree with the same structure, attributes,
        and schema definitions, but independent of the original.

        Returns:
            A new ResourceTree that is a deep copy of this one.
        """
        # Use serialization for deep copy
        data = self.to_dict()
        cloned = ResourceTree.from_dict(data)

        # Copy schema definitions
        for key, schema in self._schema_registry.items():
            cloned._schema_registry.define(key, schema)

        return cloned

    def clone_subtree(self, path: str) -> ResourceTree:
        """Clone a subtree rooted at the given path.

        Args:
            path: Path to the resource to use as root of new tree.

        Returns:
            A new ResourceTree rooted at the specified resource.

        Raises:
            KeyError: If the path does not exist.
        """
        resource = self.get(path)
        if resource is None:
            msg = f"Path not found: {path}"
            raise KeyError(msg)

        # Serialize just this resource and its descendants
        data = self._resource_to_dict(resource)
        cloned = ResourceTree.from_dict(data)

        # Copy schema definitions
        for key, schema in self._schema_registry.items():
            cloned._schema_registry.define(key, schema)

        return cloned

    def merge(self, source: ResourceTree) -> None:
        """Merge another tree into this one.

        Recursively merges resources from source into this tree:
        - New resources are added
        - Existing resource attributes are updated from source

        Args:
            source: The tree to merge from.
        """
        self._merge_resource(self.root, source.root)

    def _merge_resource(self, target: Resource, source: Resource) -> None:
        """Recursively merge source resource into target."""
        # Merge attributes
        for key, value in source.attributes.items():
            target.set_attribute(key, value)

        # Merge children
        for name, source_child in source.children.items():
            target_child = target.get_child(name)
            if target_child is None:
                # Clone the source child and add it
                child_data = self._resource_to_dict(source_child)
                self._load_children(self, target, {name: child_data})
            else:
                # Recursively merge
                self._merge_resource(target_child, source_child)

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

        results: list[Resource] = []
        for resource in self.walk():
            if match_pattern(resource.path, pattern):
                results.append(resource)
        return results

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
        from hrcp.propagation import get_effective_value

        results: list[Any] = []
        for resource in self.query(pattern):
            value = get_effective_value(resource, key, mode)
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
        return self._resource_to_dict(self._root)

    def _resource_to_dict(self, resource: Resource) -> dict[str, Any]:
        """Recursively serialize a Resource to a dict."""
        return {
            "name": resource.name,
            "attributes": dict(resource.attributes),
            "children": {
                name: self._resource_to_dict(child)
                for name, child in resource.children.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceTree:
        """Create a ResourceTree from a dictionary.

        Args:
            data: A dict representation of the tree.

        Returns:
            A new ResourceTree with the data.
        """
        tree = cls(root_name=data["name"])
        # Set root attributes
        for key, value in data.get("attributes", {}).items():
            tree._root._attributes[key] = value  # Bypass validation for load
        # Recursively create children
        cls._load_children(tree, tree._root, data.get("children", {}))
        return tree

    @classmethod
    def _load_children(
        cls,
        tree: ResourceTree,
        parent: Resource,
        children_data: dict[str, dict[str, Any]],
    ) -> None:
        """Recursively load children from dict data."""
        for child_data in children_data.values():
            child = Resource(
                name=child_data["name"],
                schema_registry=tree._schema_registry,
            )
            # Set attributes bypassing validation
            for key, value in child_data.get("attributes", {}).items():
                child._attributes[key] = value
            parent.add_child(child)
            # Recurse for grandchildren
            cls._load_children(tree, child, child_data.get("children", {}))

    def to_json(self, path: str, indent: int = 2) -> None:
        """Save the tree to a JSON file.

        Args:
            path: Path to the output JSON file.
            indent: Indentation level for human-readable output.
        """
        import json

        data = self.to_dict()
        with open(path, "w") as f:
            json.dump(data, f, indent=indent)

    @classmethod
    def from_json(cls, path: str) -> ResourceTree:
        """Load a ResourceTree from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            A new ResourceTree loaded from the file.
        """
        import json

        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_yaml(self, path: str | None = None) -> str:
        """Serialize the tree to a YAML string.

        Args:
            path: Optional file path to write to. If None, returns string.

        Returns:
            A YAML string representation of the tree.
        """
        import yaml

        data = self.to_dict()
        yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False)

        if path is not None:
            from pathlib import Path

            Path(path).write_text(yaml_str)

        return yaml_str

    @classmethod
    def from_yaml(cls, yaml_str: str) -> ResourceTree:
        """Create a ResourceTree from a YAML string.

        Args:
            yaml_str: A YAML string representation of the tree.

        Returns:
            A new ResourceTree with the data.
        """
        import yaml

        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    @classmethod
    def from_yaml_file(cls, path: str) -> ResourceTree:
        """Create a ResourceTree from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            A new ResourceTree loaded from the file.
        """
        from pathlib import Path

        yaml_str = Path(path).read_text()
        return cls.from_yaml(yaml_str)

    def to_toml(self, path: str | None = None) -> str:
        """Serialize the tree to a TOML string.

        TOML format uses nested tables for children. Root attributes
        are at top level, children become [table] sections.

        Args:
            path: Optional file path to write to. If None, returns string.

        Returns:
            A TOML string representation of the tree.
        """
        import tomli_w

        data = self._to_toml_dict(self.root)
        toml_str = tomli_w.dumps(data)

        if path is not None:
            from pathlib import Path

            Path(path).write_text(toml_str)

        return toml_str

    def _to_toml_dict(self, resource: Resource) -> dict[str, Any]:
        """Convert resource to TOML-compatible dict."""
        result: dict[str, Any] = {}

        # Add attributes at this level
        for key, value in resource.attributes.items():
            result[key] = value

        # Add children as nested dicts
        for name, child in resource.children.items():
            result[name] = self._to_toml_dict(child)

        return result

    @classmethod
    def from_toml(cls, toml_str: str, root_name: str = "root") -> ResourceTree:
        """Create a ResourceTree from a TOML string.

        Args:
            toml_str: A TOML string.
            root_name: Name for the root resource.

        Returns:
            A new ResourceTree with the data.
        """
        import tomllib

        data = tomllib.loads(toml_str)
        return cls._from_toml_dict(data, root_name)

    @classmethod
    def _from_toml_dict(cls, data: dict[str, Any], root_name: str) -> ResourceTree:
        """Create tree from TOML-style dict."""
        tree = cls(root_name=root_name)

        for key, value in data.items():
            if isinstance(value, dict):
                # This is a child resource
                cls._load_toml_child(tree, tree.root, key, value)
            else:
                # This is an attribute
                tree.root.set_attribute(key, value)

        return tree

    @classmethod
    def _load_toml_child(
        cls, tree: ResourceTree, parent: Resource, name: str, data: dict[str, Any]
    ) -> None:
        """Recursively load TOML child resources."""
        from hrcp.core import Resource

        child = Resource(name=name, schema_registry=tree._schema_registry)
        parent.add_child(child)

        for key, value in data.items():
            if isinstance(value, dict):
                cls._load_toml_child(tree, child, key, value)
            else:
                child.set_attribute(key, value)

    @classmethod
    def from_toml_file(cls, path: str, root_name: str = "root") -> ResourceTree:
        """Create a ResourceTree from a TOML file.

        Args:
            path: Path to the TOML file.
            root_name: Name for the root resource.

        Returns:
            A new ResourceTree loaded from the file.
        """
        from pathlib import Path

        toml_str = Path(path).read_text()
        return cls.from_toml(toml_str, root_name)

    def find(self, path: str | None = None, **criteria: Any) -> list[Resource]:
        """Find resources matching attribute criteria.

        Args:
            path: Optional path to restrict search to a subtree.
            **criteria: Attribute key-value pairs to match.

        Returns:
            List of resources where all criteria match.
        """
        results = []
        start = self.get(path) if path else self.root

        if start is None:
            return results

        for resource in self._walk_resource(start):
            if self._matches_criteria(resource, criteria):
                results.append(resource)

        return results

    def find_first(self, path: str | None = None, **criteria: Any) -> Resource | None:
        """Find first resource matching attribute criteria.

        Args:
            path: Optional path to restrict search to a subtree.
            **criteria: Attribute key-value pairs to match.

        Returns:
            First matching resource, or None if not found.
        """
        start = self.get(path) if path else self.root

        if start is None:
            return None

        for resource in self._walk_resource(start):
            if self._matches_criteria(resource, criteria):
                return resource

        return None

    def filter(
        self,
        predicate: Callable[[Resource], bool],
        path: str | None = None,
    ) -> list[Resource]:
        """Filter resources using a predicate function.

        Args:
            predicate: Function that takes a Resource and returns True to include.
            path: Optional path to restrict search to a subtree.

        Returns:
            List of resources where predicate returns True.
        """
        results = []
        start = self.get(path) if path else self.root

        if start is None:
            return results

        for resource in self._walk_resource(start):
            if predicate(resource):
                results.append(resource)

        return results

    def exists(self, path: str | None = None, **criteria: Any) -> bool:
        """Check if any resource matches the criteria.

        Args:
            path: Optional path to restrict search to a subtree.
            **criteria: Attribute key-value pairs to match.

        Returns:
            True if at least one matching resource exists.
        """
        return self.find_first(path=path, **criteria) is not None

    def count(self, path: str | None = None, **criteria: Any) -> int:
        """Count resources matching the criteria.

        Args:
            path: Optional path to restrict search to a subtree.
            **criteria: Attribute key-value pairs to match.

        Returns:
            Number of matching resources.
        """
        return len(self.find(path=path, **criteria))

    def _matches_criteria(self, resource: Resource, criteria: dict[str, Any]) -> bool:
        """Check if resource matches all criteria."""
        for key, value in criteria.items():
            if resource.attributes.get(key) != value:
                return False
        return True

    def depth(self) -> int:
        """Get the maximum depth of the tree.

        Returns:
            Maximum depth (1 for root only, 2 for root with children, etc.)
        """
        return self._resource_depth(self.root)

    def _resource_depth(self, resource: Resource) -> int:
        """Calculate depth of subtree rooted at resource."""
        if not resource.children:
            return 1
        return 1 + max(self._resource_depth(c) for c in resource.children.values())

    def attribute_keys(self) -> set[str]:
        """Get all unique attribute keys used in the tree.

        Returns:
            Set of all attribute key names.
        """
        keys: set[str] = set()
        for resource in self.walk():
            keys.update(resource.attributes.keys())
        return keys

    def pretty(self, path: str | None = None, *, compact: bool = False) -> str:
        """Get a pretty-printed string representation of the tree.

        Args:
            path: Optional path to restrict to a subtree.
            compact: If True, use compact format without attributes.

        Returns:
            A formatted string representation of the tree.
        """
        start = self.get(path) if path else self.root
        if start is None:
            return ""

        lines: list[str] = []
        self._pretty_resource(start, lines, "", compact)
        return "\n".join(lines)

    def _pretty_resource(
        self,
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

            self._pretty_resource(child, lines, child_prefix, compact, is_root=False)

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

    def copy(self, source_path: str, dest_path: str) -> Resource:
        """Copy a resource (and its subtree) to a new path.

        Args:
            source_path: Path of resource to copy.
            dest_path: Destination path for the copy.

        Returns:
            The newly created resource.

        Raises:
            KeyError: If source path doesn't exist.
        """
        source = self.get(source_path)
        if source is None:
            msg = f"Source path not found: {source_path}"
            raise KeyError(msg)

        # Serialize and recreate at new location
        data = self._resource_to_dict(source)

        # Extract destination parent and new name
        from hrcp.path import basename
        from hrcp.path import parent_path

        dest_parent_path = parent_path(dest_path)
        new_name = basename(dest_path)

        # Update name in data
        data["name"] = new_name

        # Get or create parent
        dest_parent = self.get(dest_parent_path)
        if dest_parent is None:
            dest_parent = self.create(dest_parent_path)

        # Create the copy
        return self._create_from_dict(data, dest_parent)

    def _create_from_dict(self, data: dict[str, Any], parent: Resource) -> Resource:
        """Create resource from dict and attach to parent."""
        resource = Resource(
            name=data["name"],
            schema_registry=self._schema_registry,
        )
        for key, value in data.get("attributes", {}).items():
            resource._attributes[key] = value

        parent.add_child(resource)

        # Recursively create children
        for child_data in data.get("children", {}).values():
            self._create_from_dict(child_data, resource)

        return resource

    def move(self, source_path: str, dest_path: str) -> Resource:
        """Move a resource (and its subtree) to a new path.

        Args:
            source_path: Path of resource to move.
            dest_path: Destination path.

        Returns:
            The moved resource at its new location.

        Raises:
            KeyError: If source path doesn't exist.
        """
        # Copy then delete original
        result = self.copy(source_path, dest_path)
        self.delete(source_path)
        return result

    def rename(self, path: str, new_name: str) -> Resource:
        """Rename a resource in place.

        Args:
            path: Path to the resource to rename.
            new_name: New name for the resource.

        Returns:
            The renamed resource.

        Raises:
            KeyError: If path doesn't exist.
        """
        resource = self.get(path)
        if resource is None:
            msg = f"Path not found: {path}"
            raise KeyError(msg)

        parent = resource.parent
        if parent is None:
            # Can't rename root
            msg = "Cannot rename root resource"
            raise ValueError(msg)

        # Remove from parent with old name
        del parent._children[resource.name]

        # Update name and re-add
        resource._name = new_name
        parent._children[new_name] = resource

        return resource

    def __repr__(self) -> str:
        """Return a string representation of the ResourceTree."""
        return f"ResourceTree(root={self._root.name!r}, size={len(self)})"
