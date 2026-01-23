"""Tests for HRCP serialization - save/load tree state."""

import json
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from hrcp.core import ResourceTree

# Strategy for valid resource names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)

# Strategy for attribute values (JSON-serializable)
attr_value = st.one_of(
    st.integers(),
    st.text(max_size=50),
    st.booleans(),
)


class TestToDict:
    """Test ResourceTree.to_dict() serialization."""

    @given(root=valid_name)
    def test_empty_tree_to_dict(self, root):
        """An empty tree serializes to a dict with root."""
        tree = ResourceTree(root_name=root)

        data = tree.to_dict()

        assert data["name"] == root
        assert data["attributes"] == {}
        assert data["children"] == {}

    @given(
        root=valid_name,
        key1=valid_name,
        key2=valid_name,
        val1=st.text(max_size=20),
        val2=st.text(max_size=20),
    )
    def test_tree_with_attributes_to_dict(self, root, key1, key2, val1, val2):
        """Attributes are preserved in serialization."""
        if key1 == key2:
            key2 = key2 + "2"
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute(key1, val1)
        tree.root.set_attribute(key2, val2)

        data = tree.to_dict()

        assert data["attributes"][key1] == val1
        assert data["attributes"][key2] == val2

    @given(
        root=valid_name,
        region=valid_name,
        server=valid_name,
        name_val=st.text(max_size=20),
        port_val=st.integers(),
    )
    def test_tree_with_children_to_dict(self, root, region, server, name_val, port_val):
        """Children are serialized recursively."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{region}", attributes={"name": name_val})
        tree.create(f"/{root}/{region}/{server}", attributes={"port": port_val})

        data = tree.to_dict()

        assert region in data["children"]
        region_data = data["children"][region]
        assert region_data["attributes"]["name"] == name_val
        assert server in region_data["children"]
        assert region_data["children"][server]["attributes"]["port"] == port_val

    @given(root=valid_name, child1=valid_name, child2=valid_name)
    def test_to_dict_preserves_all_data(self, root, child1, child2):
        """All tree data is preserved in serialization."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child1}/b/c", attributes={"deep": True})
        tree.create(f"/{root}/{child2}", attributes={"shallow": True})

        data = tree.to_dict()

        # Verify structure preserved
        assert child1 in data["children"]
        assert child2 in data["children"]
        assert data["children"][child2]["attributes"]["shallow"] is True


class TestFromDict:
    """Test ResourceTree.from_dict() deserialization."""

    @given(root=valid_name, version=st.text(max_size=10))
    def test_from_dict_creates_tree(self, root, version):
        """from_dict creates a ResourceTree from a dict."""
        data = {
            "name": root,
            "attributes": {"version": version},
            "children": {},
        }

        tree = ResourceTree.from_dict(data)

        assert tree.root.name == root
        assert tree.root.attributes["version"] == version

    @given(root=valid_name, region=valid_name, server=valid_name, port=st.integers())
    def test_from_dict_recreates_children(self, root, region, server, port):
        """from_dict recreates the full tree structure."""
        data = {
            "name": root,
            "attributes": {},
            "children": {
                region: {
                    "name": region,
                    "attributes": {"name": "us-east"},
                    "children": {
                        server: {
                            "name": server,
                            "attributes": {"port": port},
                            "children": {},
                        }
                    },
                }
            },
        }

        tree = ResourceTree.from_dict(data)

        resource = tree.get(f"/{root}/{region}/{server}")
        assert resource is not None
        assert resource.attributes["port"] == port

    @given(root=valid_name, child1=valid_name, child2=valid_name, val=st.integers())
    def test_roundtrip_preserves_tree(self, root, child1, child2, val):
        """to_dict followed by from_dict preserves the tree."""
        if child1 == child2:
            child2 = child2 + "2"
        original = ResourceTree(root_name=root)
        original.create(f"/{root}/{child1}/b", attributes={"value": val})
        original.create(f"/{root}/{child2}/y/z", attributes={"nested": True})
        original.root.set_attribute("top", "level")

        data = original.to_dict()
        restored = ResourceTree.from_dict(data)

        # Verify structure
        assert restored.root.name == root
        assert restored.root.attributes["top"] == "level"
        assert restored.get(f"/{root}/{child1}/b").attributes["value"] == val
        assert restored.get(f"/{root}/{child2}/y/z").attributes["nested"] is True


class TestToJson:
    """Test ResourceTree.to_json() file serialization."""

    @given(root=valid_name, version=st.text(min_size=1, max_size=10))
    def test_to_json_creates_file(self, root, version):
        """to_json creates a JSON file."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("version", version)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            tree.to_json(path)

            # Verify file exists and is valid JSON
            with Path(path).open() as f:
                data = json.load(f)

            assert data["name"] == root
            assert data["attributes"]["version"] == version
        finally:
            Path(path).unlink(missing_ok=True)

    @given(root=valid_name)
    def test_to_json_is_human_readable(self, root):
        """to_json produces indented, human-readable output."""
        tree = ResourceTree(root_name=root)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            tree.to_json(path)

            with Path(path).open() as f:
                content = f.read()

            # Should be indented (multiple lines)
            assert content.count("\n") > 1
        finally:
            Path(path).unlink(missing_ok=True)


class TestFromJson:
    """Test ResourceTree.from_json() file deserialization."""

    @given(root=valid_name, version=st.text(min_size=1, max_size=10))
    def test_from_json_loads_tree(self, root, version):
        """from_json loads a tree from a JSON file."""
        data = {
            "name": root,
            "attributes": {"version": version},
            "children": {},
        }

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(data, f)
            path = f.name

        try:
            tree = ResourceTree.from_json(path)

            assert tree.root.name == root
            assert tree.root.attributes["version"] == version
        finally:
            Path(path).unlink(missing_ok=True)

    @given(
        root=valid_name,
        child1=valid_name,
        child2=valid_name,
        host=st.text(min_size=1, max_size=20),
        port=st.integers(),
    )
    def test_json_roundtrip(self, root, child1, child2, host, port):
        """to_json followed by from_json preserves the tree."""
        if child1 == child2:
            child2 = child2 + "2"
        original = ResourceTree(root_name=root)
        original.create(f"/{root}/{child1}", attributes={"host": host, "port": port})
        original.create(f"/{root}/{child2}", attributes={"ttl": 300})

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            original.to_json(path)
            restored = ResourceTree.from_json(path)

            assert restored.root.name == root
            db = restored.get(f"/{root}/{child1}")
            assert db.attributes["host"] == host
            assert db.attributes["port"] == port
        finally:
            Path(path).unlink(missing_ok=True)


class TestComplexTypes:
    """Test serialization of complex attribute types."""

    @given(root=valid_name, host=st.text(min_size=1, max_size=20), port=st.integers())
    def test_nested_dict_attributes(self, root, host, port):
        """Nested dicts in attributes are preserved."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("settings", {"db": {"host": host, "port": port}})

        data = tree.to_dict()
        restored = ResourceTree.from_dict(data)

        settings = restored.root.attributes["settings"]
        assert settings["db"]["host"] == host
        assert settings["db"]["port"] == port

    @given(
        root=valid_name,
        tags=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5),
    )
    def test_list_attributes(self, root, tags):
        """Lists in attributes are preserved."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("tags", tags)

        data = tree.to_dict()
        restored = ResourceTree.from_dict(data)

        assert restored.root.attributes["tags"] == tags

    @given(root=valid_name)
    def test_null_values(self, root):
        """None values in attributes are preserved."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("optional", None)

        data = tree.to_dict()
        restored = ResourceTree.from_dict(data)

        assert "optional" in restored.root.attributes
        assert restored.root.attributes["optional"] is None
