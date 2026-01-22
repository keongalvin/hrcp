"""Tests for the ResourceTree class - the container for HRCP hierarchy."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hrcp.core import Resource
from hrcp.core import ResourceTree

# Strategy for valid resource names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)

# Strategy for attribute values
attr_value = st.one_of(
    st.integers(),
    st.text(max_size=50),
    st.booleans(),
)


class TestResourceTreeCreation:
    """Test ResourceTree instantiation."""

    @given(root_name=valid_name)
    def test_create_tree_with_root_name(self, root_name):
        """A ResourceTree can be created with a root name."""
        tree = ResourceTree(root_name=root_name)
        assert tree.root is not None
        assert tree.root.name == root_name

    def test_create_tree_with_default_root_name(self):
        """A ResourceTree has a default root name if not specified."""
        tree = ResourceTree()
        assert tree.root.name == "root"

    @given(root_name=valid_name)
    def test_root_is_a_resource(self, root_name):
        """The tree's root is a Resource instance."""
        tree = ResourceTree(root_name=root_name)
        assert isinstance(tree.root, Resource)

    @given(root_name=valid_name)
    def test_root_has_no_parent(self, root_name):
        """The root Resource has no parent."""
        tree = ResourceTree(root_name=root_name)
        assert tree.root.parent is None


class TestResourceTreePathAccess:
    """Test accessing Resources by path."""

    @given(root_name=valid_name)
    def test_get_root_by_path(self, root_name):
        """The root can be accessed by '/' path."""
        tree = ResourceTree(root_name=root_name)
        result = tree.get("/")
        assert result is tree.root

    @given(root_name=valid_name)
    def test_get_root_by_name_path(self, root_name):
        """The root can be accessed by '/root_name' path."""
        tree = ResourceTree(root_name=root_name)
        result = tree.get(f"/{root_name}")
        assert result is tree.root

    @given(root_name=valid_name, child_name=valid_name)
    def test_get_child_by_path(self, root_name, child_name):
        """A child Resource can be accessed by path."""
        tree = ResourceTree(root_name=root_name)
        child = Resource(name=child_name)
        tree.root.add_child(child)

        result = tree.get(f"/{root_name}/{child_name}")

        assert result is child

    @given(names=st.lists(valid_name, min_size=2, max_size=5, unique=True))
    def test_get_deeply_nested_resource(self, names):
        """Deeply nested Resources can be accessed by path."""
        root_name = names[0]
        tree = ResourceTree(root_name=root_name)

        # Build chain
        parent = tree.root
        for name in names[1:]:
            child = Resource(name=name)
            parent.add_child(child)
            parent = child

        path = "/" + "/".join(names)
        result = tree.get(path)

        assert result is parent  # Last resource in chain

    @given(root_name=valid_name, fake_path=valid_name)
    def test_get_nonexistent_path_returns_none(self, root_name, fake_path):
        """Getting a nonexistent path returns None."""
        tree = ResourceTree(root_name=root_name)

        result = tree.get(f"/{fake_path}/nonexistent")

        assert result is None

    @given(root_name=valid_name, child_name=valid_name, missing=valid_name)
    def test_get_partial_path_returns_none_if_incomplete(self, root_name, child_name, missing):
        """If only part of the path exists, None is returned."""
        tree = ResourceTree(root_name=root_name)
        child = Resource(name=child_name)
        tree.root.add_child(child)

        result = tree.get(f"/{root_name}/{child_name}/{missing}")

        assert result is None


class TestResourceTreeCreationAtPath:
    """Test creating Resources at specific paths."""

    @given(root_name=valid_name, child_name=valid_name)
    def test_create_resource_at_path(self, root_name, child_name):
        """A Resource can be created at a specific path."""
        tree = ResourceTree(root_name=root_name)

        resource = tree.create(f"/{root_name}/{child_name}")

        assert resource.name == child_name
        assert resource.parent is tree.root
        assert tree.root.get_child(child_name) is resource

    @given(root_name=valid_name, child_name=valid_name, key=valid_name, value=attr_value)
    def test_create_resource_with_attributes(self, root_name, child_name, key, value):
        """A Resource can be created with initial attributes."""
        tree = ResourceTree(root_name=root_name)

        resource = tree.create(f"/{root_name}/{child_name}", attributes={key: value})

        assert resource.attributes == {key: value}

    @given(root_name=valid_name, names=st.lists(valid_name, min_size=2, max_size=4, unique=True))
    def test_create_nested_path_creates_intermediates(self, root_name, names):
        """Creating a deep path creates intermediate Resources."""
        tree = ResourceTree(root_name=root_name)
        path = f"/{root_name}/" + "/".join(names)

        leaf = tree.create(path)

        # Verify the full chain was created
        for i in range(len(names)):
            partial_path = f"/{root_name}/" + "/".join(names[:i+1])
            assert tree.get(partial_path) is not None
        assert tree.get(path) is leaf

    @given(root_name=valid_name, child_name=valid_name)
    def test_create_at_existing_path_raises(self, root_name, child_name):
        """Creating at an existing path raises ValueError."""
        tree = ResourceTree(root_name=root_name)
        tree.create(f"/{root_name}/{child_name}")

        with pytest.raises(ValueError, match="already exists"):
            tree.create(f"/{root_name}/{child_name}")

    @given(root_name=valid_name, wrong_root=valid_name, child_name=valid_name)
    def test_create_with_wrong_root_raises(self, root_name, wrong_root, child_name):
        """Creating with a path that doesn't start with root raises."""
        if wrong_root == root_name:
            wrong_root = wrong_root + "x"
        tree = ResourceTree(root_name=root_name)

        with pytest.raises(ValueError, match="must start with"):
            tree.create(f"/{wrong_root}/{child_name}")


class TestResourceTreeDeletion:
    """Test deleting Resources from the tree."""

    @given(root_name=valid_name, child_name=valid_name)
    def test_delete_leaf_resource(self, root_name, child_name):
        """A leaf Resource can be deleted by path."""
        tree = ResourceTree(root_name=root_name)
        tree.create(f"/{root_name}/{child_name}")

        deleted = tree.delete(f"/{root_name}/{child_name}")

        assert deleted.name == child_name
        assert tree.get(f"/{root_name}/{child_name}") is None

    @given(root_name=valid_name, names=st.lists(valid_name, min_size=2, max_size=4, unique=True))
    def test_delete_subtree(self, root_name, names):
        """Deleting a Resource deletes its entire subtree."""
        tree = ResourceTree(root_name=root_name)
        path = f"/{root_name}/" + "/".join(names)
        tree.create(path)

        # Delete the first child (should delete entire subtree)
        tree.delete(f"/{root_name}/{names[0]}")

        for i in range(len(names)):
            partial_path = f"/{root_name}/" + "/".join(names[:i+1])
            assert tree.get(partial_path) is None

    @given(root_name=valid_name, fake_name=valid_name)
    def test_delete_nonexistent_path_raises(self, root_name, fake_name):
        """Deleting a nonexistent path raises KeyError."""
        tree = ResourceTree(root_name=root_name)

        with pytest.raises(KeyError):
            tree.delete(f"/{root_name}/{fake_name}")

    @given(root_name=valid_name)
    def test_cannot_delete_root(self, root_name):
        """The root cannot be deleted."""
        tree = ResourceTree(root_name=root_name)

        with pytest.raises(ValueError, match="cannot delete root"):
            tree.delete(f"/{root_name}")


class TestResourceTreeTraversal:
    """Test tree traversal operations."""

    @given(root_name=valid_name, child_names=st.lists(valid_name, min_size=1, max_size=4, unique=True))
    def test_walk_visits_all_resources(self, root_name, child_names):
        """walk() yields all Resources in the tree."""
        tree = ResourceTree(root_name=root_name)
        for name in child_names:
            tree.create(f"/{root_name}/{name}")

        paths = [r.path for r in tree.walk()]

        assert f"/{root_name}" in paths
        for name in child_names:
            assert f"/{root_name}/{name}" in paths
        assert len(paths) == 1 + len(child_names)

    @given(root_name=valid_name, region=valid_name, children=st.lists(valid_name, min_size=1, max_size=3, unique=True))
    def test_walk_from_specific_path(self, root_name, region, children):
        """walk() can start from a specific path."""
        tree = ResourceTree(root_name=root_name)
        tree.create(f"/{root_name}/{region}")
        for child in children:
            tree.create(f"/{root_name}/{region}/{child}")
        tree.create(f"/{root_name}/other")

        paths = [r.path for r in tree.walk(f"/{root_name}/{region}")]

        assert f"/{root_name}/{region}" in paths
        for child in children:
            assert f"/{root_name}/{region}/{child}" in paths
        assert f"/{root_name}/other" not in paths

    @given(root_name=valid_name, fake_name=valid_name)
    def test_walk_nonexistent_path_raises(self, root_name, fake_name):
        """walk() from nonexistent path raises KeyError."""
        if root_name == fake_name:
            fake_name = fake_name + "x"
        tree = ResourceTree(root_name=root_name)

        with pytest.raises(KeyError):
            list(tree.walk(f"/{fake_name}"))


class TestResourceTreeSize:
    """Test tree size/count operations."""

    @given(root_name=valid_name)
    def test_empty_tree_has_size_one(self, root_name):
        """An empty tree has size 1 (just root)."""
        tree = ResourceTree(root_name=root_name)
        assert len(tree) == 1

    @given(root_name=valid_name, child_names=st.lists(valid_name, min_size=1, max_size=5, unique=True))
    def test_tree_size_counts_all_resources(self, root_name, child_names):
        """len(tree) returns total Resource count."""
        tree = ResourceTree(root_name=root_name)
        for name in child_names:
            tree.create(f"/{root_name}/{name}")

        assert len(tree) == 1 + len(child_names)
