"""Tests for HRCP tree pretty printing."""

from hypothesis import given
from hypothesis import strategies as st

from hrcp import ResourceTree

# Strategy for valid resource names (alphanumeric only)
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=20,
)

# Strategy for safe string values (alphanumeric only)
safe_string = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=20,
)

# Strategy for attribute values
attr_value = st.one_of(
    st.integers(),
    safe_string,
    st.booleans(),
)


class TestPrettyPrint:
    """Test tree pretty printing."""

    @given(root=valid_name, env=safe_string)
    def test_pretty_simple(self, root, env):
        """pretty() returns string representation of tree."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("env", env)

        output = tree.pretty()

        assert root in output
        assert "env" in output
        assert env in output

    @given(root=valid_name, child=valid_name, grandchild=valid_name)
    def test_pretty_nested(self, root, child, grandchild):
        """pretty() shows nested structure with indentation."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")
        tree.create(f"/{root}/{child}/{grandchild}")

        output = tree.pretty()

        # Should show hierarchy
        assert root in output
        assert child in output
        assert grandchild in output

    @given(root=valid_name, child=valid_name, host=safe_string, port=st.integers())
    def test_pretty_with_attributes(self, root, child, host, port):
        """pretty() shows attributes."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}", attributes={"host": host, "port": port})

        output = tree.pretty()

        assert "host" in output
        assert host in output
        assert "port" in output
        assert str(port) in output

    @given(root=valid_name, child1=valid_name, child2=valid_name)
    def test_pretty_compact(self, root, child1, child2):
        """pretty(compact=True) shows compact format."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child1}")
        tree.create(f"/{root}/{child2}")

        output = tree.pretty(compact=True)

        # Compact format should still have essential info
        assert root in output

    @given(root=valid_name, child=valid_name, grandchild=valid_name, other=valid_name)
    def test_pretty_subtree(self, root, child, grandchild, other):
        """pretty(path=...) shows only subtree."""
        # Ensure names don't collide
        if child == other:
            other = other + "other"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}/{grandchild}")
        tree.create(f"/{root}/{other}")

        output = tree.pretty(path=f"/{root}/{child}")

        assert child in output
        assert grandchild in output

    @given(root=valid_name, key=valid_name, value=attr_value)
    def test_pretty_with_various_attr_types(self, root, key, value):
        """pretty() handles various attribute types."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute(key, value)

        output = tree.pretty()

        assert root in output
        assert key in output

    @given(root=valid_name, fake=valid_name)
    def test_pretty_with_invalid_path_returns_empty(self, root, fake):
        """pretty() with invalid path returns empty string."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/child")

        output = tree.pretty(path=f"/{fake}")

        assert output == ""


class TestRepr:
    """Test __repr__ for debugging."""

    @given(root=valid_name, value=st.integers())
    def test_resource_repr(self, root, value):
        """Resource has useful repr."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute("x", value)

        repr_str = repr(tree.root)

        assert root in repr_str

    @given(root=valid_name, child=valid_name)
    def test_tree_repr(self, root, child):
        """ResourceTree has useful repr."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")

        repr_str = repr(tree)

        assert "ResourceTree" in repr_str
        assert root in repr_str
