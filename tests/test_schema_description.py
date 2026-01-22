"""Tests for HRCP schema description/documentation support."""

from hypothesis import given
from hypothesis import strategies as st

from hrcp import PropertySchema
from hrcp import SchemaRegistry

# Strategy for valid names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)


class TestPropertySchemaDescription:
    """Test PropertySchema description field."""

    @given(description=st.text(min_size=1, max_size=100))
    def test_schema_accepts_description(self, description):
        """PropertySchema accepts a description."""
        schema = PropertySchema(type_=int, description=description)
        assert schema.description == description

    def test_schema_description_is_none_by_default(self):
        """PropertySchema.description is None if not specified."""
        schema = PropertySchema(type_=int)
        assert schema.description is None


class TestSchemaRegistryDescription:
    """Test SchemaRegistry with descriptions."""

    @given(key=valid_name, description=st.text(min_size=1, max_size=100))
    def test_define_with_description(self, key, description):
        """Can define schema with description."""
        registry = SchemaRegistry()
        registry.define(key, type_=int, description=description)

        schema = registry.get(key)
        assert schema.description == description


class TestJSONSchemaDescriptionExport:
    """Test JSON Schema export includes descriptions."""

    @given(key=valid_name, description=st.text(min_size=1, max_size=100))
    def test_json_schema_includes_description(self, key, description):
        """to_json_schema() includes description."""
        registry = SchemaRegistry()
        registry.define(key, type_=int, description=description)

        schema = registry.to_json_schema()
        prop = schema["properties"][key]

        assert prop["description"] == description

    @given(key=valid_name)
    def test_json_schema_omits_none_description(self, key):
        """to_json_schema() omits description when None."""
        registry = SchemaRegistry()
        registry.define(key, type_=int)

        schema = registry.to_json_schema()
        prop = schema["properties"][key]

        assert "description" not in prop


class TestSchemaDocumentation:
    """Test generating documentation from schemas."""

    def test_to_markdown_generates_docs(self):
        """to_markdown() generates documentation for all schemas."""
        registry = SchemaRegistry()
        registry.define(
            "max_deposit",
            type_=int,
            ge=0,
            le=1000000,
            default=10000,
            description="Maximum deposit amount in cents",
        )
        registry.define(
            "env",
            choices=("dev", "staging", "prod"),
            default="dev",
            description="Deployment environment",
        )

        md = registry.to_markdown()

        # Check structure
        assert "# Schema Documentation" in md
        assert "## max_deposit" in md
        assert "## env" in md

        # Check content
        assert "Maximum deposit amount" in md
        assert "integer" in md.lower() or "int" in md.lower()
        assert "10000" in md  # default
        assert "dev" in md
        assert "staging" in md
        assert "prod" in md
