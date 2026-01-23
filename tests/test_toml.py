"""Tests for HRCP TOML serialization."""

import tempfile
import tomllib
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from hrcp import ResourceTree

# Strategy for valid resource names (ASCII alphanumeric, starting with letter for TOML tables)
valid_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=20,
).filter(lambda s: s[0].isalpha())  # TOML tables must start with letter

# Strategy for TOML-safe string values (ASCII alphanumeric only)
safe_string = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=20,
)

# Strategy for attribute values (TOML-serializable)
attr_value = st.one_of(
    st.integers(),
    safe_string,
    st.booleans(),
)


class TestTOMLExport:
    """Test TOML export functionality."""

    @given(root=valid_name, name=safe_string, port=st.integers(min_value=1, max_value=65535))
    def test_to_toml_returns_string(self, root, name, port):
        """to_toml() returns a TOML string."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("name", name)
        tree.root.set_attribute("port", port)

        toml_str = tree.to_toml()

        assert isinstance(toml_str, str)
        assert len(toml_str) > 0
        # Should be parseable back
        data = tomllib.loads(toml_str)
        assert "name" in data or "port" in data

    @given(root=valid_name, child=valid_name, value=st.integers())
    def test_to_toml_nested(self, root, child, value):
        """to_toml() exports nested structure."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}", attributes={"value": value})

        toml_str = tree.to_toml()

        data = tomllib.loads(toml_str)
        assert child in data
        assert data[child]["value"] == value

    @given(root=valid_name, tags=st.lists(safe_string, min_size=1, max_size=3))
    def test_to_toml_list_values(self, root, tags):
        """to_toml() handles list values."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("tags", tags)

        toml_str = tree.to_toml()

        data = tomllib.loads(toml_str)
        assert data["tags"] == tags

    @given(root=valid_name, value=safe_string)
    def test_to_toml_writes_file(self, root, value):
        """to_toml(path=...) writes to a file."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("version", value)

        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name

        try:
            tree.to_toml(path=path)

            content = Path(path).read_text()
            assert len(content) > 0
            data = tomllib.loads(content)
            assert "version" in data
        finally:
            Path(path).unlink(missing_ok=True)


class TestTOMLImport:
    """Test TOML import functionality."""

    @given(root=valid_name, name=safe_string, port=st.integers())
    def test_from_toml_simple(self, root, name, port):
        """from_toml() creates tree from TOML string."""
        toml_str = f'''
name = "{name}"
port = {port}
'''
        tree = ResourceTree.from_toml(toml_str, root_name=root)

        assert tree.root.attributes["name"] == name
        assert tree.root.attributes["port"] == port

    @given(root=valid_name, child=valid_name, host=safe_string, port=st.integers())
    def test_from_toml_nested(self, root, child, host, port):
        """from_toml() handles nested tables."""
        toml_str = f'''
[{child}]
host = "{host}"
port = {port}
'''
        tree = ResourceTree.from_toml(toml_str, root_name=root)

        resource = tree.get(f"/{root}/{child}")
        assert resource is not None
        assert resource.attributes["host"] == host
        assert resource.attributes["port"] == port


class TestTOMLRoundTrip:
    """Test TOML serialization round-trip."""

    @given(root=valid_name, name=safe_string, debug=st.booleans())
    def test_toml_round_trip_preserves_data(self, root, name, debug):
        """Tree -> TOML -> Tree preserves basic data."""
        original = ResourceTree(root_name=root)
        original.root.set_attribute("name", name)
        original.root.set_attribute("debug", debug)

        toml_str = original.to_toml()
        restored = ResourceTree.from_toml(toml_str, root_name=root)

        # Check attributes preserved
        assert restored.root.attributes["name"] == name
        assert restored.root.attributes["debug"] is debug

    @given(root=valid_name, child=valid_name, host=safe_string, port=st.integers())
    def test_toml_round_trip_nested(self, root, child, host, port):
        """Tree with children -> TOML -> Tree preserves structure."""
        original = ResourceTree(root_name=root)
        original.create(f"/{root}/{child}", attributes={"host": host, "port": port})

        toml_str = original.to_toml()
        restored = ResourceTree.from_toml(toml_str, root_name=root)

        server = restored.get(f"/{root}/{child}")
        assert server.attributes["host"] == host
        assert server.attributes["port"] == port

    @given(root=valid_name, child=valid_name, value=attr_value)
    def test_toml_file_round_trip(self, root, child, value):
        """Tree -> TOML file -> Tree preserves data."""
        original = ResourceTree(root_name=root)
        original.create(f"/{root}/{child}", attributes={"value": value})

        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name

        try:
            original.to_toml(path=path)
            restored = ResourceTree.from_toml_file(path, root_name=root)

            resource = restored.get(f"/{root}/{child}")
            assert resource.attributes["value"] == value
        finally:
            Path(path).unlink(missing_ok=True)
