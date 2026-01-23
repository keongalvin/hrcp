"""Tests for HRCP YAML serialization."""

import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from hrcp import ResourceTree

# YAML reserved words to avoid
YAML_RESERVED = {
    "null",
    "true",
    "false",
    "yes",
    "no",
    "on",
    "off",
    "Null",
    "True",
    "False",
    "Yes",
    "No",
    "On",
    "Off",
    "NULL",
    "TRUE",
    "FALSE",
    "YES",
    "NO",
    "ON",
    "OFF",
}

# Strategy for valid resource names (ASCII alphanumeric, starting with letter, avoiding YAML reserved)
valid_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=20,
).filter(lambda s: s[0].isalpha() and s not in YAML_RESERVED)

# Strategy for safe string values (same constraints as valid_name for YAML safety)
safe_string = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=20,
).filter(lambda s: s[0].isalpha() and s not in YAML_RESERVED)

# Strategy for attribute values
attr_value = st.one_of(
    st.integers(),
    safe_string,
    st.booleans(),
)


class TestYAMLExport:
    """Test YAML export functionality."""

    @given(
        root=valid_name,
        name=safe_string,
        port=st.integers(min_value=1, max_value=65535),
    )
    def test_to_yaml_returns_string(self, root, name, port):
        """to_yaml() returns a YAML string."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("name", name)
        tree.root.set_attribute("port", port)

        yaml_str = tree.to_yaml()

        assert isinstance(yaml_str, str)
        assert len(yaml_str) > 0
        # Should be parseable back
        import yaml

        data = yaml.safe_load(yaml_str)
        assert data["name"] == root

    @given(root=valid_name, child=valid_name, value=st.integers())
    def test_to_yaml_nested(self, root, child, value):
        """to_yaml() exports nested structure."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}", attributes={"value": value})

        yaml_str = tree.to_yaml()

        import yaml

        data = yaml.safe_load(yaml_str)
        assert child in data["children"]
        assert data["children"][child]["attributes"]["value"] == value

    @given(root=valid_name, tags=st.lists(safe_string, min_size=1, max_size=5))
    def test_to_yaml_list_values(self, root, tags):
        """to_yaml() handles list values."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("tags", tags)

        yaml_str = tree.to_yaml()

        import yaml

        data = yaml.safe_load(yaml_str)
        assert data["attributes"]["tags"] == tags

    @given(root=valid_name, value=safe_string)
    def test_to_yaml_writes_file(self, root, value):
        """to_yaml(path=...) writes to a file."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("version", value)

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            path = f.name

        try:
            tree.to_yaml(path=path)

            content = Path(path).read_text()
            assert len(content) > 0

            import yaml

            data = yaml.safe_load(content)
            assert data["name"] == root
        finally:
            Path(path).unlink(missing_ok=True)


class TestYAMLImport:
    """Test YAML import functionality."""

    @given(root=valid_name, app=safe_string, port=st.integers())
    def test_from_yaml_simple(self, root, app, port):
        """from_yaml() creates tree from YAML string."""
        yaml_str = f"""
name: {root}
attributes:
  app: {app}
  port: {port}
children: {{}}
"""
        tree = ResourceTree.from_yaml(yaml_str)

        assert tree.root.name == root
        assert tree.root.attributes["app"] == app
        assert tree.root.attributes["port"] == port

    @given(root=valid_name, child=valid_name, host=safe_string, port=st.integers())
    def test_from_yaml_nested(self, root, child, host, port):
        """from_yaml() handles nested children."""
        yaml_str = f"""
name: {root}
attributes: {{}}
children:
  {child}:
    name: {child}
    attributes:
      host: {host}
      port: {port}
    children: {{}}
"""
        tree = ResourceTree.from_yaml(yaml_str)

        resource = tree.get(f"/{root}/{child}")
        assert resource is not None
        assert resource.attributes["host"] == host
        assert resource.attributes["port"] == port


class TestYAMLRoundTrip:
    """Test YAML serialization round-trip."""

    @given(
        root=valid_name,
        child=valid_name,
        grandchild=valid_name,
        name_val=safe_string,
        size=st.integers(),
        role=safe_string,
        env=safe_string,
    )
    def test_yaml_round_trip_preserves_data(
        self, root, child, grandchild, name_val, size, role, env
    ):
        """Tree -> YAML -> Tree preserves all data."""
        original = ResourceTree(root_name=root)
        original.create(f"/{root}/{child}", attributes={"name": name_val, "size": size})
        original.create(f"/{root}/{child}/{grandchild}", attributes={"role": role})
        original.root.set_attribute("env", env)

        yaml_str = original.to_yaml()
        restored = ResourceTree.from_yaml(yaml_str)

        # Check structure preserved
        assert restored.root.name == root
        assert restored.root.attributes["env"] == env
        assert restored.get(f"/{root}/{child}").attributes["name"] == name_val
        assert restored.get(f"/{root}/{child}").attributes["size"] == size
        assert restored.get(f"/{root}/{child}/{grandchild}").attributes["role"] == role

    @given(root=valid_name, child=valid_name, value=attr_value)
    def test_yaml_file_round_trip(self, root, child, value):
        """Tree -> YAML file -> Tree preserves data."""
        original = ResourceTree(root_name=root)
        original.create(f"/{root}/{child}", attributes={"value": value})

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            path = f.name

        try:
            original.to_yaml(path=path)
            restored = ResourceTree.from_yaml_file(path)

            assert restored.root.name == root
            resource = restored.get(f"/{root}/{child}")
            assert resource.attributes["value"] == value
        finally:
            Path(path).unlink(missing_ok=True)
