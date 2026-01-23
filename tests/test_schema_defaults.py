"""Tests for HRCP schema default values."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hrcp import PropertySchema
from hrcp import ResourceTree
from hrcp import SchemaRegistry

# Strategy for valid names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)


class TestPropertySchemaDefault:
    """Test PropertySchema default value support."""

    @given(default=st.integers())
    def test_schema_has_default_field(self, default):
        """PropertySchema accepts a default value."""
        schema = PropertySchema(type_=int, default=default)
        assert schema.default == default

    def test_schema_default_is_none_by_default(self):
        """PropertySchema.default is None if not specified."""
        schema = PropertySchema(type_=int)
        assert schema.default is None

    @given(default=st.sampled_from(["dev", "staging", "prod"]))
    def test_schema_default_with_choices(self, default):
        """Default value works with choices constraint."""
        schema = PropertySchema(choices=("dev", "staging", "prod"), default=default)
        assert schema.default == default


class TestSchemaRegistryDefaults:
    """Test SchemaRegistry with default values."""

    @given(key=valid_name, default=st.integers())
    def test_define_with_default(self, key, default):
        """Can define schema with default value."""
        registry = SchemaRegistry()
        registry.define(key, type_=int, default=default)

        schema = registry.get(key)
        assert schema.default == default

    @given(
        key1=valid_name, key2=valid_name, default1=st.integers(), default2=st.booleans()
    )
    def test_get_default_returns_default_value(self, key1, key2, default1, default2):
        """get_default() returns the default value for a key."""
        if key1 == key2:
            key2 = key2 + "2"
        registry = SchemaRegistry()
        registry.define(key1, type_=int, default=default1)
        registry.define(key2, type_=bool, default=default2)

        assert registry.get_default(key1) == default1
        assert registry.get_default(key2) == default2

    @given(key=valid_name)
    def test_get_default_returns_none_for_undefined_key(self, key):
        """get_default() returns None for undefined keys."""
        registry = SchemaRegistry()
        assert registry.get_default(key) is None

    @given(key=valid_name)
    def test_get_default_returns_none_when_no_default(self, key):
        """get_default() returns None when schema has no default."""
        registry = SchemaRegistry()
        registry.define(key, type_=int)  # No default

        assert registry.get_default(key) is None


class TestResourceTreeWithDefaults:
    """Test ResourceTree using schema defaults."""

    @given(root=valid_name, key=valid_name, default=st.integers())
    def test_get_attribute_or_default(self, root, key, default):
        """get_attribute_or_default uses schema default when attribute not set."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=int, default=default)

        # Attribute not set - should return default
        value = tree.get_attribute_or_default(f"/{root}", key)
        assert value == default

    @given(root=valid_name, key=valid_name, default=st.integers(), actual=st.integers())
    def test_get_attribute_or_default_returns_set_value(
        self, root, key, default, actual
    ):
        """get_attribute_or_default returns actual value when attribute is set."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=int, default=default)
        tree.root.set_attribute(key, actual)

        value = tree.get_attribute_or_default(f"/{root}", key)
        assert value == actual

    @given(root=valid_name, key=valid_name)
    def test_get_attribute_or_default_none_when_no_default(self, root, key):
        """get_attribute_or_default returns None when no default and not set."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=int)  # No default

        value = tree.get_attribute_or_default(f"/{root}", key)
        assert value is None

    @given(root=valid_name, key=valid_name, default=st.integers(), fake=valid_name)
    def test_get_attribute_or_default_invalid_path(self, root, key, default, fake):
        """get_attribute_or_default raises for invalid path."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=int, default=default)

        with pytest.raises(KeyError):
            tree.get_attribute_or_default(f"/{fake}", key)


class TestJSONSchemaDefaultExport:
    """Test JSON Schema export includes default values."""

    @given(key=valid_name, default=st.integers())
    def test_json_schema_includes_default(self, key, default):
        """to_json_schema() includes default values."""
        registry = SchemaRegistry()
        registry.define(key, type_=int, default=default)

        schema = registry.to_json_schema()
        prop = schema["properties"][key]

        assert prop["default"] == default

    @given(key=valid_name)
    def test_json_schema_omits_none_default(self, key):
        """to_json_schema() omits default when it's None."""
        registry = SchemaRegistry()
        registry.define(key, type_=int)  # No default

        schema = registry.to_json_schema()
        prop = schema["properties"][key]

        assert "default" not in prop
