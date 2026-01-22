"""Schema validation for HRCP - enforce constraints on attribute values.

Provides PropertySchema for defining validation rules and SchemaRegistry
for managing schemas across a ResourceTree.
"""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


class ValidationError(Exception):
    """Raised when a value fails schema validation."""


@dataclass
class PropertySchema:
    """Defines validation constraints for a configuration attribute.

    Attributes:
        type_: Expected Python type (e.g., int, str, float).
        choices: Tuple of allowed values.
        ge: Minimum value (greater than or equal).
        le: Maximum value (less than or equal).
        validator: Custom validation function that returns True if valid.
        coerce: If True, attempt type coercion before validation.
        default: Default value when attribute is not set.
        description: Human-readable description for documentation.
        required: If True, the attribute must be present.
    """

    type_: type | None = None
    choices: tuple[Any, ...] | None = None
    ge: Any | None = None
    le: Any | None = None
    validator: Callable[[Any], bool] | None = None
    coerce: bool = False
    default: Any | None = None
    description: str | None = None
    required: bool = False


def validate_value(
    value: Any,
    schema: PropertySchema,
    key: str,
    path: str = "",
) -> None:
    """Validate a value against a PropertySchema.

    Args:
        value: The value to validate.
        schema: The schema containing constraints.
        key: The attribute key (for error messages).
        path: Optional resource path (for error messages).

    Raises:
        ValidationError: If the value violates any constraint.
    """
    location = f"'{key}'" if not path else f"'{key}' at {path}"

    # Type validation
    if schema.type_ is not None and not isinstance(value, schema.type_):
        msg = (
            f"Value for {location} must be {schema.type_.__name__}, "
            f"got {type(value).__name__}: {value!r}"
        )
        raise ValidationError(msg)

    # Choices validation
    if schema.choices is not None and value not in schema.choices:
        msg = f"Value for {location} must be one of {schema.choices}, got {value!r}"
        raise ValidationError(msg)

    # Range validation (ge)
    if schema.ge is not None and value < schema.ge:
        msg = f"Value for {location} must be >= {schema.ge}, got {value!r}"
        raise ValidationError(msg)

    # Range validation (le)
    if schema.le is not None and value > schema.le:
        msg = f"Value for {location} must be <= {schema.le}, got {value!r}"
        raise ValidationError(msg)

    # Custom validator
    if schema.validator is not None and not schema.validator(value):
        msg = f"Value for {location} failed custom validation: {value!r}"
        raise ValidationError(msg)


class SchemaRegistry:
    """Registry for PropertySchemas, mapping attribute keys to their schemas.

    Example:
        >>> registry = SchemaRegistry()
        >>> registry.define("port", type_=int, ge=1, le=65535)
        >>> registry.define("env", choices=("dev", "staging", "prod"))
    """

    def __init__(self) -> None:
        """Create a new SchemaRegistry."""
        self._schemas: dict[str, PropertySchema] = {}

    def define(
        self,
        key: str,
        schema: PropertySchema | None = None,
        **kwargs: Any,
    ) -> None:
        """Register a schema for an attribute key.

        Can pass either a PropertySchema instance or keyword arguments
        that will be used to create one.

        Args:
            key: The attribute key.
            schema: Optional PropertySchema instance.
            **kwargs: If schema is None, used to create PropertySchema.
        """
        if schema is None:
            schema = PropertySchema(**kwargs)
        self._schemas[key] = schema

    def get(self, key: str) -> PropertySchema | None:
        """Get the schema for an attribute key.

        Args:
            key: The attribute key.

        Returns:
            The PropertySchema, or None if not registered.
        """
        return self._schemas.get(key)

    def validate(self, key: str, value: Any, path: str = "") -> None:
        """Validate a value against the schema for a key.

        If no schema is registered for the key, validation passes.

        Args:
            key: The attribute key.
            value: The value to validate.
            path: Optional resource path for error messages.

        Raises:
            ValidationError: If validation fails.
        """
        schema = self.get(key)
        if schema is not None:
            validate_value(value, schema, key, path)

    def items(self) -> Iterator[tuple[str, PropertySchema]]:
        """Iterate over all (key, schema) pairs.

        Returns:
            Iterator of (attribute_key, PropertySchema) tuples.
        """
        return iter(self._schemas.items())

    def keys(self) -> Iterator[str]:
        """Iterate over all registered attribute keys.

        Returns:
            Iterator of attribute key strings.
        """
        return iter(self._schemas.keys())

    def values(self) -> Iterator[PropertySchema]:
        """Iterate over all PropertySchema instances.

        Returns:
            Iterator of PropertySchema objects.
        """
        return iter(self._schemas.values())

    def __len__(self) -> int:
        """Return the number of registered schemas."""
        return len(self._schemas)

    def __contains__(self, key: str) -> bool:
        """Check if a key has a registered schema."""
        return key in self._schemas

    def get_default(self, key: str) -> Any | None:
        """Get the default value for an attribute key.

        Args:
            key: The attribute key.

        Returns:
            The default value, or None if no schema or no default.
        """
        schema = self.get(key)
        if schema is None:
            return None
        return schema.default

    def required_fields(self) -> list[str]:
        """Get list of all required field names.

        Returns:
            List of attribute keys where required=True.
        """
        return [key for key, schema in self._schemas.items() if schema.required]

    def to_json_schema(self) -> dict[str, Any]:
        """Export all schemas as a JSON Schema document.

        Returns:
            A dict conforming to JSON Schema draft 2020-12.
        """
        properties = {}
        for key, schema in self._schemas.items():
            properties[key] = self._schema_to_json_schema(schema)

        result = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": properties,
        }

        # Add required array if any fields are required
        required = self.required_fields()
        if required:
            result["required"] = required

        return result

    def _schema_to_json_schema(self, schema: PropertySchema) -> dict[str, Any]:
        """Convert a PropertySchema to JSON Schema property definition."""
        result: dict[str, Any] = {}

        # Type mapping
        if schema.type_ is not None:
            type_map = {
                int: "integer",
                float: "number",
                str: "string",
                bool: "boolean",
                list: "array",
                dict: "object",
            }
            result["type"] = type_map.get(schema.type_, "string")

        # Constraints
        if schema.ge is not None:
            result["minimum"] = schema.ge
        if schema.le is not None:
            result["maximum"] = schema.le

        # Choices -> enum
        if schema.choices is not None:
            result["enum"] = list(schema.choices)

        # Default value
        if schema.default is not None:
            result["default"] = schema.default

        # Description
        if schema.description is not None:
            result["description"] = schema.description

        return result

    def to_markdown(self) -> str:
        """Generate Markdown documentation for all schemas.

        Returns:
            A Markdown string documenting all registered schemas.
        """
        lines = ["# Schema Documentation", ""]

        type_names = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        for key, schema in sorted(self._schemas.items()):
            lines.append(f"## {key}")
            lines.append("")

            if schema.description:
                lines.append(schema.description)
                lines.append("")

            # Type
            if schema.type_ is not None:
                type_name = type_names.get(schema.type_, str(schema.type_))
                lines.append(f"- **Type**: {type_name}")

            # Constraints
            if schema.ge is not None:
                lines.append(f"- **Minimum**: {schema.ge}")
            if schema.le is not None:
                lines.append(f"- **Maximum**: {schema.le}")

            # Choices
            if schema.choices is not None:
                choices_str = ", ".join(repr(c) for c in schema.choices)
                lines.append(f"- **Choices**: {choices_str}")

            # Default
            if schema.default is not None:
                lines.append(f"- **Default**: {schema.default!r}")

            lines.append("")

        return "\n".join(lines)
