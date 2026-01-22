"""Tests for HRCP YAML serialization.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

from hrcp import ResourceTree


class TestYAMLExport:
    """Test YAML export functionality."""

    def test_to_yaml_simple(self):
        """to_yaml() exports simple tree to YAML string."""
        tree = ResourceTree(root_name="config")
        tree.root.set_attribute("name", "myapp")
        tree.root.set_attribute("port", 8080)

        yaml_str = tree.to_yaml()

        assert "name:" in yaml_str
        assert "myapp" in yaml_str
        assert "port:" in yaml_str
        assert "8080" in yaml_str

    def test_to_yaml_nested(self):
        """to_yaml() exports nested structure."""
        tree = ResourceTree(root_name="config")
        tree.create("/config/database", attributes={"host": "localhost", "port": 5432})

        yaml_str = tree.to_yaml()

        assert "database:" in yaml_str
        assert "host:" in yaml_str
        assert "localhost" in yaml_str

    def test_to_yaml_list_values(self):
        """to_yaml() handles list values."""
        tree = ResourceTree(root_name="config")
        tree.root.set_attribute("tags", ["web", "api", "backend"])

        yaml_str = tree.to_yaml()

        assert "tags:" in yaml_str
        assert "- web" in yaml_str or "web" in yaml_str


class TestYAMLImport:
    """Test YAML import functionality."""

    def test_from_yaml_simple(self):
        """from_yaml() creates tree from YAML string."""
        yaml_str = """
name: config
attributes:
  app: myapp
  port: 8080
children: {}
"""
        tree = ResourceTree.from_yaml(yaml_str)

        assert tree.root.name == "config"
        assert tree.root.attributes["app"] == "myapp"
        assert tree.root.attributes["port"] == 8080

    def test_from_yaml_nested(self):
        """from_yaml() handles nested children."""
        yaml_str = """
name: config
attributes: {}
children:
  database:
    name: database
    attributes:
      host: localhost
      port: 5432
    children: {}
"""
        tree = ResourceTree.from_yaml(yaml_str)

        db = tree.get("/config/database")
        assert db is not None
        assert db.attributes["host"] == "localhost"
        assert db.attributes["port"] == 5432


class TestYAMLRoundTrip:
    """Test YAML serialization round-trip."""

    def test_yaml_round_trip_preserves_data(self):
        """Tree -> YAML -> Tree preserves all data."""
        original = ResourceTree(root_name="org")
        original.create("/org/team", attributes={"name": "backend", "size": 5})
        original.create("/org/team/alice", attributes={"role": "lead"})
        original.root.set_attribute("env", "prod")

        yaml_str = original.to_yaml()
        restored = ResourceTree.from_yaml(yaml_str)

        # Check structure preserved
        assert restored.root.name == "org"
        assert restored.root.attributes["env"] == "prod"
        assert restored.get("/org/team").attributes["name"] == "backend"
        assert restored.get("/org/team/alice").attributes["role"] == "lead"
