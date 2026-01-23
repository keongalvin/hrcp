"""Tests for HRCP validation reporting."""

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


class TestValidationReport:
    """Test validation reporting for entire tree."""

    @given(root=valid_name, port=st.integers(min_value=1, max_value=65535))
    def test_validate_all_returns_empty_when_valid(self, root, port):
        """validate_all() returns empty dict when all valid."""
        tree = ResourceTree(root_name=root)
        tree.define("port", type_=int, required=True)
        tree.root.set_attribute("port", port)

        errors = tree.validate_all()

        assert errors == {}

    @given(root=valid_name, child=valid_name, key=valid_name)
    def test_validate_all_returns_missing_required(self, root, child, key):
        """validate_all() returns dict of paths to missing required fields."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=str, required=True)
        tree.create(f"/{root}/{child}")

        errors = tree.validate_all()

        # Both root and child are missing the required key
        assert f"/{root}" in errors
        assert key in errors[f"/{root}"]
        assert f"/{root}/{child}" in errors
        assert key in errors[f"/{root}/{child}"]

    @given(
        root=valid_name,
        child=valid_name,
        grandchild=valid_name,
        name=st.text(min_size=1, max_size=20),
    )
    def test_validate_all_checks_nested_resources(self, root, child, grandchild, name):
        """validate_all() checks all nested resources."""
        tree = ResourceTree(root_name=root)
        tree.define("name", type_=str, required=True)
        tree.create(f"/{root}/{child}", attributes={"name": name})
        tree.create(f"/{root}/{child}/{grandchild}")  # Missing name

        errors = tree.validate_all()

        # root and grandchild missing name, child has it
        assert f"/{root}" in errors
        assert f"/{root}/{child}" not in errors
        assert f"/{root}/{child}/{grandchild}" in errors

    @given(
        root=valid_name,
        child1=valid_name,
        child2=valid_name,
        id_val=st.text(min_size=1, max_size=10),
    )
    def test_validate_all_with_path(self, root, child1, child2, id_val):
        """validate_all(path=...) validates only subtree."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.define("id", required=True)
        tree.create(f"/{root}/{child1}")  # Missing id
        tree.create(f"/{root}/{child2}", attributes={"id": id_val})

        errors = tree.validate_all(path=f"/{root}/{child2}")

        # Only child2 subtree checked, and it's valid
        assert errors == {}

    @given(root=valid_name, port=st.integers(min_value=1, max_value=65535))
    def test_is_valid_returns_bool(self, root, port):
        """is_valid() returns True if no validation errors."""
        tree = ResourceTree(root_name=root)
        tree.define("port", type_=int, required=True)

        assert tree.is_valid() is False

        tree.root.set_attribute("port", port)
        assert tree.is_valid() is True

    @given(root=valid_name, child=valid_name, key=valid_name, value=attr_value)
    def test_validate_all_passes_with_all_values_set(self, root, child, key, value):
        """validate_all() passes when all required values are set."""
        tree = ResourceTree(root_name=root)
        tree.define(key, required=True)
        tree.root.set_attribute(key, value)
        tree.create(f"/{root}/{child}", attributes={key: value})

        errors = tree.validate_all()

        assert errors == {}


class TestValidationSummary:
    """Test validation summary output."""

    @given(root=valid_name, child=valid_name, key=valid_name)
    def test_validation_summary(self, root, child, key):
        """validation_summary() returns human-readable report."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=str, required=True, description="Required field")
        tree.create(f"/{root}/{child}")

        summary = tree.validation_summary()

        assert key in summary
        assert f"/{root}" in summary
        assert f"/{root}/{child}" in summary

    @given(root=valid_name, key=valid_name, value=st.text(min_size=1, max_size=20))
    def test_validation_summary_empty_when_valid(self, root, key, value):
        """validation_summary() returns empty or success message when valid."""
        tree = ResourceTree(root_name=root)
        tree.define(key, type_=str, required=True)
        tree.root.set_attribute(key, value)

        summary = tree.validation_summary()

        # Either empty or indicates no errors
        assert key not in summary or "error" not in summary.lower()


class TestValidateAllWithInvalidPath:
    """Test validate_all with invalid paths."""

    @given(root=valid_name, fake=valid_name, key=valid_name)
    def test_validate_all_with_invalid_path_returns_empty(self, root, fake, key):
        """validate_all() with invalid path returns empty dict."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)
        tree.define(key, required=True)
        tree.create(f"/{root}/child")  # Missing required

        errors = tree.validate_all(path=f"/{fake}")

        assert errors == {}
