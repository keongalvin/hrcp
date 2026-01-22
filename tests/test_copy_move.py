"""Tests for HRCP copy and move operations.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hrcp import ResourceTree

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


class TestCopyResource:
    """Test copying resources within tree."""

    @given(root=valid_name, src=valid_name, dest=valid_name, key=valid_name, val=attr_value)
    def test_copy_resource_to_new_path(self, root, src, dest, key, val):
        """copy() copies resource to new location."""
        if src == dest:
            dest = dest + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{src}", attributes={key: val, "active": True})

        tree.copy(f"/{root}/{src}", f"/{root}/{dest}")

        # Original still exists
        assert tree.get(f"/{root}/{src}") is not None
        # Copy exists with same attributes
        instance = tree.get(f"/{root}/{dest}")
        assert instance is not None
        assert instance.attributes[key] == val
        assert instance.attributes["active"] is True

    @given(root=valid_name, src=valid_name, dest=valid_name, child1=valid_name, child2=valid_name)
    def test_copy_with_children(self, root, src, dest, child1, child2):
        """copy() copies entire subtree."""
        if src == dest:
            dest = dest + "2"
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{src}/{child1}", attributes={"x": 1})
        tree.create(f"/{root}/{src}/{child2}", attributes={"y": 2})

        tree.copy(f"/{root}/{src}", f"/{root}/{dest}")

        assert tree.get(f"/{root}/{dest}/{child1}") is not None
        assert tree.get(f"/{root}/{dest}/{child2}") is not None
        assert tree.get(f"/{root}/{dest}/{child1}").attributes["x"] == 1

    @given(root=valid_name, src=valid_name, dest=valid_name, val1=st.integers(), val2=st.integers())
    def test_copy_is_independent(self, root, src, dest, val1, val2):
        """Copied resource is independent of original."""
        if src == dest:
            dest = dest + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{src}", attributes={"value": val1})

        tree.copy(f"/{root}/{src}", f"/{root}/{dest}")

        # Modify original
        tree.get(f"/{root}/{src}").set_attribute("value", val2)

        # Copy unchanged
        assert tree.get(f"/{root}/{dest}").attributes["value"] == val1

    @given(root=valid_name, fake=valid_name, dest=valid_name)
    def test_copy_invalid_source_raises(self, root, fake, dest):
        """copy() raises KeyError for invalid source path."""
        tree = ResourceTree(root_name=root)

        with pytest.raises(KeyError):
            tree.copy(f"/{root}/{fake}", f"/{root}/{dest}")


class TestMoveResource:
    """Test moving resources within tree."""

    @given(root=valid_name, src=valid_name, dest=valid_name, val=attr_value)
    def test_move_resource(self, root, src, dest, val):
        """move() moves resource to new location."""
        if src == dest:
            dest = dest + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{src}", attributes={"data": val})

        tree.move(f"/{root}/{src}", f"/{root}/{dest}")

        # Old path no longer exists
        assert tree.get(f"/{root}/{src}") is None
        # New path exists with attributes
        assert tree.get(f"/{root}/{dest}") is not None
        assert tree.get(f"/{root}/{dest}").attributes["data"] == val

    @given(root=valid_name, src=valid_name, dest=valid_name, child=valid_name, val=st.integers())
    def test_move_with_children(self, root, src, dest, child, val):
        """move() moves entire subtree."""
        if src == dest:
            dest = dest + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{src}/{child}", attributes={"x": val})

        tree.move(f"/{root}/{src}", f"/{root}/{dest}")

        assert tree.get(f"/{root}/{src}") is None
        assert tree.get(f"/{root}/{dest}/{child}") is not None
        assert tree.get(f"/{root}/{dest}/{child}").attributes["x"] == val

    @given(root=valid_name, fake=valid_name, dest=valid_name)
    def test_move_invalid_source_raises(self, root, fake, dest):
        """move() raises KeyError for invalid source path."""
        tree = ResourceTree(root_name=root)

        with pytest.raises(KeyError):
            tree.move(f"/{root}/{fake}", f"/{root}/{dest}")


class TestRename:
    """Test renaming resources."""

    @given(root=valid_name, old_name=valid_name, new_name=valid_name, val=st.integers())
    def test_rename_resource(self, root, old_name, new_name, val):
        """rename() changes resource name in place."""
        if old_name == new_name:
            new_name = new_name + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{old_name}", attributes={"x": val})

        tree.rename(f"/{root}/{old_name}", new_name)

        assert tree.get(f"/{root}/{old_name}") is None
        assert tree.get(f"/{root}/{new_name}") is not None
        assert tree.get(f"/{root}/{new_name}").attributes["x"] == val
