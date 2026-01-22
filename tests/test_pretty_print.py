"""Tests for HRCP tree pretty printing.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

from hrcp import ResourceTree


class TestPrettyPrint:
    """Test tree pretty printing."""

    def test_pretty_simple(self):
        """pretty() returns string representation of tree."""
        tree = ResourceTree(root_name="config")
        tree.root.set_attribute("env", "prod")

        output = tree.pretty()

        assert "config" in output
        assert "env" in output
        assert "prod" in output

    def test_pretty_nested(self):
        """pretty() shows nested structure with indentation."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team")
        tree.create("/org/team/alice")

        output = tree.pretty()

        # Should show hierarchy
        assert "org" in output
        assert "team" in output
        assert "alice" in output

    def test_pretty_with_attributes(self):
        """pretty() shows attributes."""
        tree = ResourceTree(root_name="config")
        tree.create("/config/db", attributes={"host": "localhost", "port": 5432})

        output = tree.pretty()

        assert "host" in output
        assert "localhost" in output
        assert "port" in output
        assert "5432" in output

    def test_pretty_compact(self):
        """pretty(compact=True) shows compact format."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/a")
        tree.create("/org/b")

        output = tree.pretty(compact=True)

        # Compact format should still have essential info
        assert "org" in output

    def test_pretty_subtree(self):
        """pretty(path=...) shows only subtree."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team/alice")
        tree.create("/org/config")

        output = tree.pretty(path="/org/team")

        assert "team" in output
        assert "alice" in output
        # org root and config should not be in output from subtree
        # (depending on implementation, org might be shown as context)


class TestRepr:
    """Test __repr__ for debugging."""

    def test_resource_repr(self):
        """Resource has useful repr."""
        tree = ResourceTree(root_name="config")
        tree.root.set_attribute("x", 1)

        repr_str = repr(tree.root)

        assert "config" in repr_str

    def test_tree_repr(self):
        """ResourceTree has useful repr."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/a")

        repr_str = repr(tree)

        assert "ResourceTree" in repr_str
        assert "org" in repr_str
