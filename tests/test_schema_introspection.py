"""Tests for HRCP schema introspection and documentation generation."""

import json

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


class TestSchemaRegistryIteration:
    """Test iterating over schema definitions."""

    @given(keys=st.lists(valid_name, min_size=3, max_size=5, unique=True))
    def test_items_returns_all_schemas(self, keys):
        """items() returns all registered key-schema pairs."""
        registry = SchemaRegistry()
        registry.define(keys[0], type_=int, ge=1, le=65535)
        registry.define(keys[1], choices=("dev", "staging", "prod"))
        registry.define(keys[2], type_=bool)

        items = dict(registry.items())

        assert len(items) == 3
        for key in keys[:3]:
            assert key in items

    def test_items_empty_registry(self):
        """items() returns empty iterator for empty registry."""
        registry = SchemaRegistry()
        assert list(registry.items()) == []

    @given(key1=valid_name, key2=valid_name)
    def test_keys_returns_all_attribute_names(self, key1, key2):
        """keys() returns all registered attribute names."""
        if key1 == key2:
            key2 = key2 + "2"
        registry = SchemaRegistry()
        registry.define(key1, type_=int)
        registry.define(key2, type_=str)

        keys = list(registry.keys())

        assert set(keys) == {key1, key2}

    @given(key=valid_name, ge=st.integers(min_value=0, max_value=100))
    def test_values_returns_all_schemas(self, key, ge):
        """values() returns all PropertySchema instances."""
        registry = SchemaRegistry()
        registry.define(key, type_=int, ge=ge)

        schemas = list(registry.values())

        assert len(schemas) == 1
        assert isinstance(schemas[0], PropertySchema)
        assert schemas[0].type_ is int

    @given(key1=valid_name, key2=valid_name)
    def test_len_returns_schema_count(self, key1, key2):
        """len() returns number of registered schemas."""
        if key1 == key2:
            key2 = key2 + "2"
        registry = SchemaRegistry()
        assert len(registry) == 0

        registry.define(key1, type_=int)
        registry.define(key2, type_=str)
        assert len(registry) == 2

    @given(key=valid_name, missing=valid_name)
    def test_contains_checks_key_exists(self, key, missing):
        """'key in registry' checks if key is defined."""
        if key == missing:
            missing = missing + "x"
        registry = SchemaRegistry()
        registry.define(key, type_=int)

        assert key in registry
        assert missing not in registry


class TestResourceTreeSchemaAccess:
    """Test accessing schema through ResourceTree."""

    @given(root=valid_name, key=valid_name, ge=st.integers(min_value=0, max_value=100))
    def test_tree_exposes_schema_registry(self, root, key, ge):
        """Tree has schema property to access registry."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=int, ge=ge)

        assert key in tree.schema
        assert tree.schema.get(key).type_ is int

    @given(root=valid_name, key1=valid_name, key2=valid_name)
    def test_tree_schema_iteration(self, root, key1, key2):
        """Can iterate over tree's schema definitions."""
        if key1 == key2:
            key2 = key2 + "2"
        tree = ResourceTree(root_name=root)
        tree.define(key1, type_=int)
        tree.define(key2, type_=bool)

        keys = list(tree.schema.keys())
        assert set(keys) == {key1, key2}


class TestJSONSchemaExport:
    """Test exporting schema as JSON Schema."""

    @given(key1=valid_name, key2=valid_name, key3=valid_name)
    def test_to_json_schema_basic(self, key1, key2, key3):
        """to_json_schema() generates valid JSON Schema."""
        keys = [key1]
        for k in [key2, key3]:
            if k in keys:
                keys.append(k + str(len(keys)))
            else:
                keys.append(k)

        registry = SchemaRegistry()
        registry.define(keys[0], type_=int, ge=1, le=65535)
        registry.define(keys[1], type_=str)
        registry.define(keys[2], type_=bool)

        schema = registry.to_json_schema()

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_json_schema_type_mapping(self):
        """Python types map to JSON Schema types correctly."""
        registry = SchemaRegistry()
        registry.define("count", type_=int)
        registry.define("rate", type_=float)
        registry.define("name", type_=str)
        registry.define("active", type_=bool)
        registry.define("items", type_=list)
        registry.define("config", type_=dict)

        schema = registry.to_json_schema()
        props = schema["properties"]

        assert props["count"]["type"] == "integer"
        assert props["rate"]["type"] == "number"
        assert props["name"]["type"] == "string"
        assert props["active"]["type"] == "boolean"
        assert props["items"]["type"] == "array"
        assert props["config"]["type"] == "object"

    @given(
        key=valid_name,
        ge=st.integers(min_value=1, max_value=100),
        le=st.integers(min_value=101, max_value=65535),
    )
    def test_json_schema_constraints(self, key, ge, le):
        """Constraints (ge, le) map to JSON Schema validation."""
        registry = SchemaRegistry()
        registry.define(key, type_=int, ge=ge, le=le)

        schema = registry.to_json_schema()
        prop_schema = schema["properties"][key]

        assert prop_schema["minimum"] == ge
        assert prop_schema["maximum"] == le

    @given(
        key=valid_name,
        choices=st.lists(
            st.text(min_size=1, max_size=10), min_size=2, max_size=4, unique=True
        ),
    )
    def test_json_schema_choices(self, key, choices):
        """Choices map to JSON Schema enum."""
        registry = SchemaRegistry()
        registry.define(key, choices=tuple(choices))

        schema = registry.to_json_schema()
        prop_schema = schema["properties"][key]

        assert prop_schema["enum"] == choices

    @given(key=valid_name, ge=st.integers(min_value=0, max_value=100))
    def test_json_schema_is_valid_json(self, key, ge):
        """Generated schema is valid JSON."""
        registry = SchemaRegistry()
        registry.define(key, type_=int, ge=ge)

        schema = registry.to_json_schema()

        # Should be serializable to JSON
        json_str = json.dumps(schema)
        assert json_str is not None

        # And back
        parsed = json.loads(json_str)
        assert parsed == schema


class TestTreeJSONSchemaExport:
    """Test JSON Schema export through ResourceTree."""

    @given(root=valid_name, key1=valid_name, key2=valid_name)
    def test_tree_to_json_schema(self, root, key1, key2):
        """Tree can export its schema as JSON Schema."""
        if key1 == key2:
            key2 = key2 + "2"
        tree = ResourceTree(root_name=root)
        tree.define(key1, type_=int, ge=0, le=1_000_000)
        tree.define(key2, choices=("USD", "EUR", "GBP"))

        schema = tree.to_json_schema()

        assert "properties" in schema
        assert key1 in schema["properties"]
        assert key2 in schema["properties"]
