"""Tests for HRCP TOML serialization.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

from hrcp import ResourceTree


class TestTOMLExport:
    """Test TOML export functionality."""

    def test_to_toml_simple(self):
        """to_toml() exports simple tree to TOML string."""
        tree = ResourceTree(root_name="config")
        tree.root.set_attribute("name", "myapp")
        tree.root.set_attribute("port", 8080)

        toml_str = tree.to_toml()

        assert 'name = "myapp"' in toml_str
        assert "port = 8080" in toml_str

    def test_to_toml_nested(self):
        """to_toml() exports nested structure as tables."""
        tree = ResourceTree(root_name="config")
        tree.create("/config/database", attributes={"host": "localhost", "port": 5432})

        toml_str = tree.to_toml()

        assert "[database]" in toml_str or "database" in toml_str
        assert 'host = "localhost"' in toml_str

    def test_to_toml_list_values(self):
        """to_toml() handles list values."""
        tree = ResourceTree(root_name="config")
        tree.root.set_attribute("tags", ["web", "api"])

        toml_str = tree.to_toml()

        assert "tags" in toml_str
        assert "web" in toml_str


class TestTOMLImport:
    """Test TOML import functionality."""

    def test_from_toml_simple(self):
        """from_toml() creates tree from TOML string."""
        toml_str = """
name = "myapp"
port = 8080
"""
        tree = ResourceTree.from_toml(toml_str, root_name="config")

        assert tree.root.attributes["name"] == "myapp"
        assert tree.root.attributes["port"] == 8080

    def test_from_toml_nested(self):
        """from_toml() handles nested tables."""
        toml_str = """
[database]
host = "localhost"
port = 5432
"""
        tree = ResourceTree.from_toml(toml_str, root_name="config")

        db = tree.get("/config/database")
        assert db is not None
        assert db.attributes["host"] == "localhost"
        assert db.attributes["port"] == 5432


class TestTOMLRoundTrip:
    """Test TOML serialization round-trip."""

    def test_toml_round_trip_preserves_data(self):
        """Tree -> TOML -> Tree preserves basic data."""
        original = ResourceTree(root_name="config")
        original.root.set_attribute("name", "myapp")
        original.root.set_attribute("debug", True)
        original.create("/config/server", attributes={"host": "0.0.0.0", "port": 8080})

        toml_str = original.to_toml()
        restored = ResourceTree.from_toml(toml_str, root_name="config")

        # Check attributes preserved
        assert restored.root.attributes["name"] == "myapp"
        assert restored.root.attributes["debug"] is True

        server = restored.get("/config/server")
        assert server.attributes["host"] == "0.0.0.0"
        assert server.attributes["port"] == 8080
