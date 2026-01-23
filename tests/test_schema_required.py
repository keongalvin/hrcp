"""Tests for HRCP schema required field support."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hrcp import PropertySchema
from hrcp import ResourceTree
from hrcp import SchemaRegistry
from hrcp import ValidationError

# Strategy for valid names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)


class TestPropertySchemaRequired:
    """Test PropertySchema required field."""

    def test_schema_accepts_required(self):
        """PropertySchema accepts required flag."""
        schema = PropertySchema(type_=int, required=True)
        assert schema.required is True

    def test_schema_required_is_false_by_default(self):
        """PropertySchema.required is False if not specified."""
        schema = PropertySchema(type_=int)
        assert schema.required is False


class TestSchemaRegistryRequired:
    """Test SchemaRegistry with required fields."""

    @given(key=valid_name)
    def test_define_required_field(self, key):
        """Can define schema as required."""
        registry = SchemaRegistry()
        registry.define(key, type_=str, required=True)

        schema = registry.get(key)
        assert schema.required is True

    @given(key1=valid_name, key2=valid_name, key3=valid_name, key4=valid_name)
    def test_required_fields_list(self, key1, key2, key3, key4):
        """required_fields() returns list of required field names."""
        keys = [key1]
        for k in [key2, key3, key4]:
            if k in keys:
                keys.append(k + str(len(keys)))
            else:
                keys.append(k)

        registry = SchemaRegistry()
        registry.define(keys[0], type_=str, required=True)
        registry.define(keys[1], type_=str, required=True)
        registry.define(keys[2], type_=int, required=False)
        registry.define(keys[3], type_=int)  # Default not required

        required = registry.required_fields()

        assert set(required) == {keys[0], keys[1]}


class TestRequiredValidation:
    """Test validation of required fields."""

    @given(root=valid_name, key=valid_name, value=st.text(min_size=1, max_size=20))
    def test_validate_required_passes_when_present(self, root, key, value):
        """Validation passes when required field is present."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=str, required=True)
        tree.root.set_attribute(key, value)

        # Should not raise
        tree.validate_required(f"/{root}")

    @given(root=valid_name, key=valid_name)
    def test_validate_required_fails_when_missing(self, root, key):
        """Validation fails when required field is missing."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=str, required=True)

        with pytest.raises(ValidationError, match=key):
            tree.validate_required(f"/{root}")

    @given(
        root=valid_name,
        key1=valid_name,
        key2=valid_name,
        value=st.text(min_size=1, max_size=20),
    )
    def test_validate_required_checks_all_fields(self, root, key1, key2, value):
        """Validation checks all required fields."""
        if key1 == key2:
            key2 = key2 + "2"
        tree = ResourceTree(root_name=root)
        tree.define(key1, type_=str, required=True)
        tree.define(key2, type_=str, required=True)
        tree.root.set_attribute(key1, value)
        # key2 is missing

        with pytest.raises(ValidationError, match=key2):
            tree.validate_required(f"/{root}")

    @given(
        root=valid_name,
        key1=valid_name,
        key2=valid_name,
        key3=valid_name,
        value=st.text(min_size=1, max_size=20),
    )
    def test_validate_required_returns_missing_list(
        self, root, key1, key2, key3, value
    ):
        """get_missing_required() returns list of missing required fields."""
        keys = [key1]
        for k in [key2, key3]:
            if k in keys:
                keys.append(k + str(len(keys)))
            else:
                keys.append(k)

        tree = ResourceTree(root_name=root)
        tree.define(keys[0], type_=str, required=True)
        tree.define(keys[1], type_=str, required=True)
        tree.define(keys[2], type_=int, required=True)
        tree.root.set_attribute(keys[0], value)

        missing = tree.get_missing_required(f"/{root}")

        assert set(missing) == {keys[1], keys[2]}

    @given(root=valid_name, fake=valid_name, key=valid_name)
    def test_get_missing_required_invalid_path_raises(self, root, fake, key):
        """get_missing_required() raises KeyError for invalid path."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)
        tree.define(key, required=True)

        with pytest.raises(KeyError):
            tree.get_missing_required(f"/{fake}")


class TestJSONSchemaRequiredExport:
    """Test JSON Schema export includes required fields."""

    @given(key1=valid_name, key2=valid_name, key3=valid_name)
    def test_json_schema_includes_required_array(self, key1, key2, key3):
        """to_json_schema() includes required array."""
        keys = [key1]
        for k in [key2, key3]:
            if k in keys:
                keys.append(k + str(len(keys)))
            else:
                keys.append(k)

        registry = SchemaRegistry()
        registry.define(keys[0], type_=str, required=True)
        registry.define(keys[1], type_=str, required=True)
        registry.define(keys[2], type_=int)

        schema = registry.to_json_schema()

        assert "required" in schema
        assert set(schema["required"]) == {keys[0], keys[1]}

    @given(key1=valid_name, key2=valid_name)
    def test_json_schema_omits_required_when_none(self, key1, key2):
        """to_json_schema() omits required when no required fields."""
        if key1 == key2:
            key2 = key2 + "2"
        registry = SchemaRegistry()
        registry.define(key1, type_=int)
        registry.define(key2, type_=int)

        schema = registry.to_json_schema()

        assert "required" not in schema
