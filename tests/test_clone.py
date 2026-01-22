"""Tests for HRCP tree cloning/copying.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hrcp import ResourceTree
from hrcp import ValidationError

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


class TestTreeClone:
    """Test ResourceTree cloning."""

    @given(root=valid_name, key=valid_name, val1=st.integers(), val2=st.integers(), child=valid_name)
    def test_clone_creates_independent_copy(self, root, key, val1, val2, child):
        """clone() creates a deep copy independent of original."""
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute(key, val1)
        tree.create(f"/{root}/{child}", attributes={"name": "test"})

        cloned = tree.clone()

        # Modify original
        tree.root.set_attribute(key, val2)
        tree.create(f"/{root}/another")

        # Clone should be unchanged
        assert cloned.root.attributes[key] == val1
        assert cloned.get(f"/{cloned.root.name}/another") is None

    @given(root=valid_name, child1=valid_name, child2=valid_name, name1=st.text(max_size=20), name2=st.text(max_size=20))
    def test_clone_preserves_structure(self, root, child1, child2, name1, name2):
        """clone() preserves full tree structure."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/team/{child1}", attributes={"name": name1})
        tree.create(f"/{root}/team/{child2}", attributes={"name": name2})

        cloned = tree.clone()

        assert cloned.get(f"/{root}/team/{child1}") is not None
        assert cloned.get(f"/{root}/team/{child1}").attributes["name"] == name1
        assert cloned.get(f"/{root}/team/{child2}").attributes["name"] == name2

    @given(root=valid_name, port=st.integers(min_value=1, max_value=65535))
    def test_clone_preserves_schema(self, root, port):
        """clone() preserves schema definitions."""
        tree = ResourceTree(root_name=root)
        tree.define("port", type_=int, ge=1, le=65535)
        tree.root.set_attribute("port", port)

        cloned = tree.clone()

        # Schema should still be enforced
        with pytest.raises(ValidationError):
            cloned.root.set_attribute("port", -1)


class TestSubtreeClone:
    """Test cloning subtrees."""

    @given(root=valid_name, team=valid_name, member1=valid_name, member2=valid_name)
    def test_clone_subtree(self, root, team, member1, member2):
        """clone_subtree() clones only specified subtree."""
        if member1 == member2:
            member2 = member2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{team}/{member1}", attributes={"role": "dev"})
        tree.create(f"/{root}/{team}/{member2}", attributes={"role": "qa"})
        tree.create(f"/{root}/config", attributes={"env": "prod"})

        subtree = tree.clone_subtree(f"/{root}/{team}")

        # Subtree has team as root
        assert subtree.root.name == team
        assert subtree.get(f"/{team}/{member1}") is not None
        assert subtree.get(f"/{team}/{member2}") is not None

        # Original config is not in subtree
        assert subtree.get(f"/{team}/config") is None

    @given(root=valid_name, fake=valid_name)
    def test_clone_subtree_invalid_path_raises(self, root, fake):
        """clone_subtree() raises for invalid path."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)

        with pytest.raises(KeyError):
            tree.clone_subtree(f"/{fake}")


class TestMergeTrees:
    """Test merging trees together."""

    @given(root=valid_name, base_key=valid_name, base_val=attr_value, new_child=valid_name)
    def test_merge_adds_missing_resources(self, root, base_key, base_val, new_child):
        """merge() adds resources from source not in target."""
        target = ResourceTree(root_name=root)
        target.root.set_attribute(base_key, base_val)

        source = ResourceTree(root_name=root)
        source.create(f"/{root}/{new_child}", attributes={"added": True})

        target.merge(source)

        assert target.get(f"/{root}/{new_child}") is not None
        assert target.get(f"/{root}/{new_child}").attributes["added"] is True
        assert target.root.attributes[base_key] == base_val

    @given(root=valid_name, key=valid_name, val1=st.integers(), val2=st.integers(), keep_key=valid_name, keep_val=attr_value)
    def test_merge_updates_existing_attributes(self, root, key, val1, val2, keep_key, keep_val):
        """merge() updates attributes from source."""
        if key == keep_key:
            keep_key = keep_key + "2"
        target = ResourceTree(root_name=root)
        target.root.set_attribute(key, val1)
        target.root.set_attribute(keep_key, keep_val)

        source = ResourceTree(root_name=root)
        source.root.set_attribute(key, val2)

        target.merge(source)

        assert target.root.attributes[key] == val2
        assert target.root.attributes[keep_key] == keep_val

    @given(root=valid_name, child=valid_name, old_val=st.text(max_size=20), new_val=st.text(max_size=20), port=st.integers())
    def test_merge_recursive(self, root, child, old_val, new_val, port):
        """merge() recursively merges children."""
        target = ResourceTree(root_name=root)
        target.create(f"/{root}/{child}", attributes={"host": old_val})

        source = ResourceTree(root_name=root)
        source.create(f"/{root}/{child}", attributes={"host": new_val, "port": port})

        target.merge(source)

        db = target.get(f"/{root}/{child}")
        assert db.attributes["host"] == new_val
        assert db.attributes["port"] == port
