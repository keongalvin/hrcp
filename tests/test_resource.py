"""Tests for the Resource class - the fundamental node in HRCP tree."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hrcp.core import Resource

# Strategy for valid resource names: non-empty, no slashes
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


class TestResourceCreation:
    """Test Resource instantiation and basic properties."""

    @given(name=valid_name)
    def test_create_resource_with_name(self, name):
        """A Resource preserves its name exactly as given."""
        resource = Resource(name=name)
        assert resource.name == name

    @given(name=valid_name, cpu=st.integers(), memory=st.text(max_size=10))
    def test_create_resource_with_attributes(self, name, cpu, memory):
        """A Resource preserves all attributes exactly as given."""
        attrs = {"cpu": cpu, "memory": memory}
        resource = Resource(name=name, attributes=attrs)
        assert resource.name == name
        assert resource.attributes == attrs

    @given(name=valid_name)
    def test_resource_has_empty_attributes_by_default(self, name):
        """A Resource without attributes has an empty dict."""
        resource = Resource(name=name)
        assert resource.attributes == {}

    @given(name=valid_name)
    def test_resource_has_no_parent_by_default(self, name):
        """A newly created Resource has no parent."""
        resource = Resource(name=name)
        assert resource.parent is None

    @given(name=valid_name)
    def test_resource_has_no_children_by_default(self, name):
        """A newly created Resource has no children."""
        resource = Resource(name=name)
        assert resource.children == {}

    def test_resource_name_cannot_be_empty(self):
        """A Resource must have a non-empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Resource(name="")

    @given(
        prefix=st.text(max_size=10),
        suffix=st.text(max_size=10),
    )
    def test_resource_name_cannot_contain_slash(self, prefix, suffix):
        """A Resource name cannot contain '/' as it's used for paths."""
        name = f"{prefix}/{suffix}"
        with pytest.raises(ValueError, match="name cannot contain '/'"):
            Resource(name=name)


class TestResourceChildren:
    """Test adding and removing children from Resources."""

    @given(parent_name=valid_name, child_name=valid_name)
    def test_add_child_to_resource(self, parent_name, child_name):
        """A child can be added to a Resource."""
        parent = Resource(name=parent_name)
        child = Resource(name=child_name)

        parent.add_child(child)

        assert child_name in parent.children
        assert parent.children[child_name] is child

    @given(parent_name=valid_name, child_name=valid_name)
    def test_child_parent_is_set_when_added(self, parent_name, child_name):
        """When a child is added, its parent reference is set."""
        parent = Resource(name=parent_name)
        child = Resource(name=child_name)

        parent.add_child(child)

        assert child.parent is parent

    @given(parent_name=valid_name, child_names=st.lists(valid_name, min_size=2, max_size=5, unique=True))
    def test_add_multiple_children(self, parent_name, child_names):
        """Multiple children can be added to a Resource."""
        parent = Resource(name=parent_name)
        for name in child_names:
            parent.add_child(Resource(name=name))

        assert len(parent.children) == len(child_names)
        for name in child_names:
            assert name in parent.children

    @given(parent_name=valid_name, child_name=valid_name)
    def test_cannot_add_duplicate_child_name(self, parent_name, child_name):
        """Cannot add two children with the same name."""
        parent = Resource(name=parent_name)
        child1 = Resource(name=child_name)
        child2 = Resource(name=child_name)

        parent.add_child(child1)

        with pytest.raises(ValueError, match="already exists"):
            parent.add_child(child2)

    @given(parent_name=valid_name, child_name=valid_name)
    def test_remove_child_from_resource(self, parent_name, child_name):
        """A child can be removed from a Resource."""
        parent = Resource(name=parent_name)
        child = Resource(name=child_name)
        parent.add_child(child)

        removed = parent.remove_child(child_name)

        assert child_name not in parent.children
        assert removed is child

    @given(parent_name=valid_name, child_name=valid_name)
    def test_removed_child_has_no_parent(self, parent_name, child_name):
        """When a child is removed, its parent is cleared."""
        parent = Resource(name=parent_name)
        child = Resource(name=child_name)
        parent.add_child(child)

        parent.remove_child(child_name)

        assert child.parent is None

    @given(parent_name=valid_name, child_name=valid_name)
    def test_remove_nonexistent_child_raises(self, parent_name, child_name):
        """Removing a child that doesn't exist raises KeyError."""
        parent = Resource(name=parent_name)

        with pytest.raises(KeyError):
            parent.remove_child(child_name)

    @given(parent_name=valid_name, child_name=valid_name)
    def test_get_child_by_name(self, parent_name, child_name):
        """A child can be retrieved by name."""
        parent = Resource(name=parent_name)
        child = Resource(name=child_name)
        parent.add_child(child)

        result = parent.get_child(child_name)

        assert result is child

    @given(parent_name=valid_name, child_name=valid_name)
    def test_get_nonexistent_child_returns_none(self, parent_name, child_name):
        """Getting a nonexistent child returns None."""
        parent = Resource(name=parent_name)

        result = parent.get_child(child_name)

        assert result is None


class TestResourcePath:
    """Test Resource path computation."""

    @given(name=valid_name)
    def test_root_resource_path(self, name):
        """A root Resource path starts with / followed by name."""
        root = Resource(name=name)
        assert root.path == f"/{name}"

    @given(parent_name=valid_name, child_name=valid_name)
    def test_child_resource_path(self, parent_name, child_name):
        """A child Resource path includes parent path."""
        parent = Resource(name=parent_name)
        child = Resource(name=child_name)
        parent.add_child(child)

        assert child.path == f"/{parent_name}/{child_name}"
        assert child.path.startswith(parent.path)

    @given(names=st.lists(valid_name, min_size=2, max_size=6, unique=True))
    def test_deeply_nested_path(self, names):
        """Path works for deeply nested Resources."""
        resources = [Resource(name=n) for n in names]
        for i in range(len(resources) - 1):
            resources[i].add_child(resources[i + 1])

        expected_path = "/" + "/".join(names)
        assert resources[-1].path == expected_path


class TestResourceAttributes:
    """Test Resource attribute operations."""

    @given(name=valid_name, key=valid_name, value=attr_value)
    def test_set_attribute(self, name, key, value):
        """An attribute can be set on a Resource."""
        resource = Resource(name=name)
        resource.set_attribute(key, value)

        assert resource.attributes[key] == value

    @given(name=valid_name, key=valid_name, value=attr_value)
    def test_get_attribute(self, name, key, value):
        """An attribute can be retrieved from a Resource."""
        resource = Resource(name=name, attributes={key: value})

        assert resource.get_attribute(key) == value

    @given(name=valid_name, key=valid_name, default=attr_value)
    def test_get_nonexistent_attribute_returns_default(self, name, key, default):
        """Getting a nonexistent attribute returns the default."""
        resource = Resource(name=name)

        assert resource.get_attribute(key) is None
        assert resource.get_attribute(key, default=default) == default

    @given(name=valid_name, key1=valid_name, key2=valid_name, val1=attr_value, val2=attr_value)
    def test_delete_attribute(self, name, key1, key2, val1, val2):
        """An attribute can be deleted from a Resource."""
        # Ensure distinct keys
        if key1 == key2:
            key2 = key2 + "2"
        resource = Resource(name=name, attributes={key1: val1, key2: val2})

        resource.delete_attribute(key1)

        assert key1 not in resource.attributes
        assert key2 in resource.attributes

    @given(name=valid_name, key=valid_name)
    def test_delete_nonexistent_attribute_raises(self, name, key):
        """Deleting a nonexistent attribute raises KeyError."""
        resource = Resource(name=name)

        with pytest.raises(KeyError):
            resource.delete_attribute(key)
