"""Tests for HRCP schema validation - enforce constraints on attribute values."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hrcp.core import Resource
from hrcp.core import ResourceTree
from hrcp.schema import PropertySchema
from hrcp.schema import SchemaRegistry
from hrcp.schema import ValidationError
from hrcp.schema import validate_value

# Strategy for valid resource names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)


class TestPropertySchema:
    """Test PropertySchema definition."""

    def test_create_schema_with_type(self):
        """A schema can specify an expected type."""
        schema = PropertySchema(type_=int)
        assert schema.type_ is int

    @given(choices=st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=5, unique=True))
    def test_create_schema_with_choices(self, choices):
        """A schema can specify allowed values."""
        schema = PropertySchema(choices=tuple(choices))
        assert schema.choices == tuple(choices)

    @given(ge=st.integers(min_value=0, max_value=50), le=st.integers(min_value=51, max_value=100))
    def test_create_schema_with_range(self, ge, le):
        """A schema can specify min/max constraints."""
        schema = PropertySchema(ge=ge, le=le)
        assert schema.ge == ge
        assert schema.le == le

    def test_create_schema_with_custom_validator(self):
        """A schema can have a custom validation function."""

        def is_even(x):
            return x % 2 == 0

        schema = PropertySchema(validator=is_even)
        assert schema.validator is is_even

    def test_schema_defaults_to_no_constraints(self):
        """A schema with no constraints accepts any value."""
        schema = PropertySchema()
        assert schema.type_ is None
        assert schema.choices is None
        assert schema.ge is None
        assert schema.le is None
        assert schema.validator is None


class TestValidateValue:
    """Test the validate_value function."""

    @given(value=st.integers(), key=valid_name)
    def test_validate_correct_type(self, value, key):
        """Valid type passes validation."""
        schema = PropertySchema(type_=int)
        validate_value(value, schema, key)  # Should not raise

    @given(value=st.text(min_size=1), key=valid_name)
    def test_validate_wrong_type_raises(self, value, key):
        """Wrong type raises ValidationError."""
        schema = PropertySchema(type_=int)
        with pytest.raises(ValidationError) as exc_info:
            validate_value(value, schema, key)
        assert key in str(exc_info.value)
        assert "int" in str(exc_info.value)

    @given(choices=st.lists(st.text(min_size=1, max_size=10), min_size=3, max_size=5, unique=True))
    def test_validate_valid_choice(self, choices):
        """Valid choice passes validation."""
        schema = PropertySchema(choices=tuple(choices))
        validate_value(choices[1], schema, "size")  # Should not raise

    @given(choices=st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=5, unique=True), invalid=st.text(min_size=1, max_size=10))
    def test_validate_invalid_choice_raises(self, choices, invalid):
        """Invalid choice raises ValidationError."""
        if invalid in choices:
            invalid = invalid + "x"
        schema = PropertySchema(choices=tuple(choices))
        with pytest.raises(ValidationError) as exc_info:
            validate_value(invalid, schema, "size")
        assert "size" in str(exc_info.value)

    @given(ge=st.integers(min_value=0, max_value=50), value=st.integers(min_value=50, max_value=100))
    def test_validate_ge_constraint(self, ge, value):
        """Value >= ge passes validation."""
        schema = PropertySchema(ge=ge)
        validate_value(value, schema, "count")  # Should not raise

    @given(ge=st.integers(min_value=1, max_value=50))
    def test_validate_ge_violation_raises(self, ge):
        """Value < ge raises ValidationError."""
        schema = PropertySchema(ge=ge)
        with pytest.raises(ValidationError) as exc_info:
            validate_value(ge - 1, schema, "count")
        assert "count" in str(exc_info.value)
        assert ">=" in str(exc_info.value)

    @given(le=st.integers(min_value=50, max_value=100), value=st.integers(min_value=0, max_value=50))
    def test_validate_le_constraint(self, le, value):
        """Value <= le passes validation."""
        schema = PropertySchema(le=le)
        validate_value(value, schema, "percent")  # Should not raise

    @given(le=st.integers(min_value=50, max_value=99))
    def test_validate_le_violation_raises(self, le):
        """Value > le raises ValidationError."""
        schema = PropertySchema(le=le)
        with pytest.raises(ValidationError) as exc_info:
            validate_value(le + 1, schema, "percent")
        assert "percent" in str(exc_info.value)
        assert "<=" in str(exc_info.value)

    @given(ge=st.integers(min_value=0, max_value=40), le=st.integers(min_value=60, max_value=100), value=st.integers(min_value=40, max_value=60))
    def test_validate_combined_ge_le(self, ge, le, value):
        """Combined range constraints work together."""
        schema = PropertySchema(ge=ge, le=le)
        validate_value(value, schema, "value")  # Should not raise

    @given(value=st.integers().filter(lambda x: x % 2 == 0))
    def test_validate_custom_validator_passes(self, value):
        """Custom validator returning True passes."""
        schema = PropertySchema(validator=lambda x: x % 2 == 0)
        validate_value(value, schema, "even")  # Should not raise

    @given(value=st.integers().filter(lambda x: x % 2 != 0))
    def test_validate_custom_validator_fails(self, value):
        """Custom validator returning False raises ValidationError."""
        schema = PropertySchema(validator=lambda x: x % 2 == 0)
        with pytest.raises(ValidationError) as exc_info:
            validate_value(value, schema, "even")
        assert "even" in str(exc_info.value)

    @given(value=st.one_of(st.text(), st.integers(), st.none(), st.dictionaries(st.text(), st.integers())))
    def test_validate_no_constraints_passes_anything(self, value):
        """Schema with no constraints accepts any value."""
        schema = PropertySchema()
        validate_value(value, schema, "key")  # Should not raise


class TestSchemaRegistry:
    """Test SchemaRegistry for managing attribute schemas."""

    @given(key=valid_name)
    def test_register_schema(self, key):
        """A schema can be registered for an attribute."""
        registry = SchemaRegistry()
        schema = PropertySchema(type_=int)

        registry.define(key, schema)

        assert registry.get(key) is schema

    @given(key=valid_name)
    def test_get_unregistered_returns_none(self, key):
        """Getting an unregistered schema returns None."""
        registry = SchemaRegistry()
        assert registry.get(key) is None

    @given(key=valid_name, ge=st.integers(min_value=0, max_value=100))
    def test_define_convenience_method(self, key, ge):
        """Can define schema with keyword arguments."""
        registry = SchemaRegistry()

        registry.define(key, type_=int, ge=ge)

        schema = registry.get(key)
        assert schema.type_ is int
        assert schema.ge == ge


class TestResourceWithSchema:
    """Test Resource attribute validation with schemas."""

    @given(name=valid_name, port=st.integers(min_value=1, max_value=65535))
    def test_resource_validates_on_set_attribute(self, name, port):
        """Setting an attribute validates against schema."""
        registry = SchemaRegistry()
        registry.define("port", type_=int, ge=1, le=65535)

        resource = Resource(name=name, schema_registry=registry)

        resource.set_attribute("port", port)  # Valid
        assert resource.attributes["port"] == port

    @given(name=valid_name)
    def test_resource_validates_rejects_wrong_type(self, name):
        """Setting wrong type raises ValidationError."""
        registry = SchemaRegistry()
        registry.define("port", type_=int, ge=1, le=65535)
        resource = Resource(name=name, schema_registry=registry)

        with pytest.raises(ValidationError):
            resource.set_attribute("port", "not-a-number")

    @given(name=valid_name)
    def test_resource_validates_rejects_out_of_range(self, name):
        """Setting out of range value raises ValidationError."""
        registry = SchemaRegistry()
        registry.define("port", type_=int, ge=1, le=65535)
        resource = Resource(name=name, schema_registry=registry)

        with pytest.raises(ValidationError):
            resource.set_attribute("port", 0)  # Below ge

    @given(name=valid_name, custom_val=st.text())
    def test_resource_without_schema_accepts_anything(self, name, custom_val):
        """Attributes without schema definition accept any value."""
        registry = SchemaRegistry()
        registry.define("port", type_=int)

        resource = Resource(name=name, schema_registry=registry)

        # Unregistered attribute accepts anything
        resource.set_attribute("custom", custom_val)
        assert resource.attributes["custom"] == custom_val

    @given(name=valid_name, port=st.integers(min_value=1, max_value=65535))
    def test_resource_validates_initial_attributes(self, name, port):
        """Initial attributes are validated on creation."""
        registry = SchemaRegistry()
        registry.define("port", type_=int)

        # Valid
        Resource(name=name, attributes={"port": port}, schema_registry=registry)

    @given(name=valid_name)
    def test_resource_rejects_invalid_initial_attributes(self, name):
        """Invalid initial attributes raise ValidationError."""
        registry = SchemaRegistry()
        registry.define("port", type_=int)

        with pytest.raises(ValidationError):
            Resource(name=name, attributes={"port": "invalid"}, schema_registry=registry)


class TestResourceTreeWithSchema:
    """Test ResourceTree-level schema management."""

    @given(root=valid_name, choice=st.sampled_from(["dev", "staging", "prod"]))
    def test_tree_define_schema(self, root, choice):
        """ResourceTree can define schemas that apply to all resources."""
        tree = ResourceTree(root_name=root)
        tree.define("environment", choices=("dev", "staging", "prod"))

        # Schema applies to resources
        tree.root.set_attribute("environment", choice)  # Valid

    @given(root=valid_name)
    def test_tree_rejects_invalid_choice(self, root):
        """Invalid choice raises ValidationError."""
        tree = ResourceTree(root_name=root)
        tree.define("environment", choices=("dev", "staging", "prod"))

        with pytest.raises(ValidationError):
            tree.root.set_attribute("environment", "invalid")

    @given(root=valid_name, child=valid_name, port=st.integers(min_value=1, max_value=65535))
    def test_tree_create_validates_attributes(self, root, child, port):
        """ResourceTree.create validates initial attributes."""
        tree = ResourceTree(root_name=root)
        tree.define("port", type_=int, ge=1, le=65535)

        # Valid
        server = tree.create(f"/{root}/{child}", attributes={"port": port})
        assert server.attributes["port"] == port

    @given(root=valid_name, child=valid_name)
    def test_tree_create_rejects_invalid_attributes(self, root, child):
        """Invalid attributes in create raise ValidationError."""
        tree = ResourceTree(root_name=root)
        tree.define("port", type_=int, ge=1, le=65535)

        with pytest.raises(ValidationError):
            tree.create(f"/{root}/{child}", attributes={"port": "invalid"})
