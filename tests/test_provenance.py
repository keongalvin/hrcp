"""Tests for HRCP provenance tracking - knowing where values came from."""

from hypothesis import given
from hypothesis import strategies as st

from hrcp.core import ResourceTree
from hrcp.propagation import PropagationMode
from hrcp.provenance import Provenance
from hrcp.provenance import get_value

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
)


class TestProvenanceDataClass:
    """Test the Provenance data structure."""

    @given(value=attr_value)
    def test_provenance_has_value(self, value):
        """Provenance contains the resolved value."""
        prov = Provenance(value=value, source_path="/root", mode=PropagationMode.NONE)
        assert prov.value == value

    @given(path=valid_name, value=st.integers())
    def test_provenance_has_source_path(self, path, value):
        """Provenance tracks which resource the value came from."""
        source = f"/root/{path}"
        prov = Provenance(value=value, source_path=source, mode=PropagationMode.DOWN)
        assert prov.source_path == source

    @given(value=attr_value)
    def test_provenance_has_mode(self, value):
        """Provenance records the propagation mode used."""
        prov = Provenance(value=value, source_path="/r", mode=PropagationMode.UP)
        assert prov.mode == PropagationMode.UP

    @given(k1=valid_name, k2=valid_name, v1=st.integers(), v2=st.integers())
    def test_provenance_for_merged_values(self, k1, k2, v1, v2):
        """Provenance for MERGE_DOWN tracks sources for each key."""
        if k1 == k2:
            k2 = k2 + "2"
        prov = Provenance(
            value={k1: v1, k2: v2},
            source_path="/root/child",
            mode=PropagationMode.MERGE_DOWN,
            key_sources={k1: "/root", k2: "/root/child"},
        )
        assert prov.key_sources == {k1: "/root", k2: "/root/child"}

    @given(values=st.lists(st.integers(), min_size=1, max_size=5))
    def test_provenance_for_aggregated_values(self, values):
        """Provenance for UP tracks all contributing sources."""
        paths = [f"/root/{i}" for i in range(len(values))]
        prov = Provenance(
            value=values,
            source_path="/root",
            mode=PropagationMode.UP,
            contributing_paths=paths,
        )
        assert prov.contributing_paths == paths


class TestProvenanceWithDown:
    """Test provenance tracking for DOWN propagation."""

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, value=st.integers()
    )
    def test_provenance_from_self(self, root_name, child_name, key, value):
        """Provenance shows value came from the resource itself."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}", attributes={key: value})

        prov = get_value(child, key, PropagationMode.DOWN, with_provenance=True)

        assert prov.value == value
        assert prov.source_path == f"/{root_name}/{child_name}"
        assert prov.mode == PropagationMode.DOWN

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, value=attr_value
    )
    def test_provenance_from_parent(self, root_name, child_name, key, value):
        """Provenance shows value inherited from parent."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, value)
        child = tree.create(f"/{root_name}/{child_name}")

        prov = get_value(child, key, PropagationMode.DOWN, with_provenance=True)

        assert prov.value == value
        assert prov.source_path == f"/{root_name}"

    @given(
        root_name=valid_name,
        mid=valid_name,
        leaf=valid_name,
        key=valid_name,
        value=attr_value,
    )
    def test_provenance_from_grandparent(self, root_name, mid, leaf, key, value):
        """Provenance tracks value through multiple levels."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, value)
        tree.create(f"/{root_name}/{mid}/{leaf}")

        server = tree.get(f"/{root_name}/{mid}/{leaf}")
        prov = get_value(server, key, PropagationMode.DOWN, with_provenance=True)

        assert prov.value == value
        assert prov.source_path == f"/{root_name}"

    @given(root_name=valid_name, child_name=valid_name, key=valid_name)
    def test_provenance_none_when_not_found(self, root_name, child_name, key):
        """Returns None provenance when value doesn't exist."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}")

        prov = get_value(child, key, PropagationMode.DOWN, with_provenance=True)

        assert prov is None


class TestProvenanceWithUp:
    """Test provenance tracking for UP aggregation."""

    @given(
        root_name=valid_name,
        child1=valid_name,
        child2=valid_name,
        key=valid_name,
        val1=st.integers(),
        val2=st.integers(),
    )
    def test_provenance_tracks_all_contributing_resources(
        self, root_name, child1, child2, key, val1, val2
    ):
        """UP provenance lists all resources that contributed values."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root_name)
        tree.create(f"/{root_name}/{child1}", attributes={key: val1})
        tree.create(f"/{root_name}/{child2}", attributes={key: val2})

        prov = get_value(tree.root, key, PropagationMode.UP, with_provenance=True)

        assert sorted(prov.value) == sorted([val1, val2])
        assert f"/{root_name}/{child1}" in prov.contributing_paths
        assert f"/{root_name}/{child2}" in prov.contributing_paths

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        root_val=attr_value,
        child_val=attr_value,
    )
    def test_provenance_up_includes_self(
        self, root_name, child_name, key, root_val, child_val
    ):
        """UP provenance includes the resource's own value if present."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, root_val)
        tree.create(f"/{root_name}/{child_name}", attributes={key: child_val})

        prov = get_value(tree.root, key, PropagationMode.UP, with_provenance=True)

        assert f"/{root_name}" in prov.contributing_paths
        assert f"/{root_name}/{child_name}" in prov.contributing_paths

    @given(root_name=valid_name, child_name=valid_name, key=valid_name)
    def test_provenance_up_empty_when_not_found(self, root_name, child_name, key):
        """UP provenance returns empty provenance when no values found."""
        tree = ResourceTree(root_name=root_name)
        tree.create(f"/{root_name}/{child_name}")

        prov = get_value(tree.root, key, PropagationMode.UP, with_provenance=True)

        assert prov.value == []
        assert prov.contributing_paths == []


class TestProvenanceWithMergeDown:
    """Test provenance tracking for MERGE_DOWN."""

    @given(root_name=valid_name, child_name=valid_name)
    def test_provenance_tracks_key_sources(self, root_name, child_name):
        """MERGE_DOWN provenance shows where each merged key came from."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute("config", {"a": 1, "b": 2})
        child = tree.create(
            f"/{root_name}/{child_name}", attributes={"config": {"b": 3, "c": 4}}
        )

        prov = get_value(
            child, "config", PropagationMode.MERGE_DOWN, with_provenance=True
        )

        assert prov.value == {"a": 1, "b": 3, "c": 4}
        assert prov.key_sources["a"] == f"/{root_name}"
        assert prov.key_sources["b"] == f"/{root_name}/{child_name}"
        assert prov.key_sources["c"] == f"/{root_name}/{child_name}"

    @given(root_name=valid_name, child_name=valid_name)
    def test_provenance_nested_key_tracking(self, root_name, child_name):
        """MERGE_DOWN tracks sources for nested keys."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(
            "config", {"logging": {"level": "INFO", "format": "json"}}
        )
        child = tree.create(
            f"/{root_name}/{child_name}",
            attributes={"config": {"logging": {"level": "DEBUG"}}},
        )

        prov = get_value(
            child, "config", PropagationMode.MERGE_DOWN, with_provenance=True
        )

        # For nested keys, use dot notation in key_sources
        assert prov.key_sources["logging.level"] == f"/{root_name}/{child_name}"
        assert prov.key_sources["logging.format"] == f"/{root_name}"


class TestProvenanceWithNone:
    """Test provenance tracking for NONE mode."""

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        parent_val=attr_value,
        child_val=attr_value,
    )
    def test_provenance_none_mode_local_only(
        self, root_name, child_name, key, parent_val, child_val
    ):
        """NONE mode provenance only considers local value."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, parent_val)
        child = tree.create(f"/{root_name}/{child_name}", attributes={key: child_val})

        prov = get_value(child, key, PropagationMode.NONE, with_provenance=True)

        assert prov.value == child_val
        assert prov.source_path == f"/{root_name}/{child_name}"

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        parent_val=attr_value,
    )
    def test_provenance_none_mode_returns_none_if_no_local(
        self, root_name, child_name, key, parent_val
    ):
        """NONE mode returns None if no local value exists."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, parent_val)
        child = tree.create(f"/{root_name}/{child_name}")

        prov = get_value(child, key, PropagationMode.NONE, with_provenance=True)

        assert prov is None


class TestProvenanceMergeDownEdgeCases:
    """Test edge cases for MERGE_DOWN provenance."""

    @given(root_name=valid_name, child_name=valid_name, key=valid_name)
    def test_merge_down_returns_none_when_no_values(self, root_name, child_name, key):
        """MERGE_DOWN returns None when attribute doesn't exist anywhere."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}")

        prov = get_value(child, key, PropagationMode.MERGE_DOWN, with_provenance=True)

        assert prov is None

    @given(root_name=valid_name, child_name=valid_name)
    def test_merge_down_deeply_nested_dict_key_tracking(self, root_name, child_name):
        """MERGE_DOWN tracks sources for deeply nested keys (3+ levels)."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(
            "config",
            {"level1": {"level2": {"level3": "root_value", "other": "root_other"}}},
        )
        child = tree.create(
            f"/{root_name}/{child_name}",
            attributes={"config": {"level1": {"level2": {"level3": "child_value"}}}},
        )

        prov = get_value(
            child, "config", PropagationMode.MERGE_DOWN, with_provenance=True
        )

        # Verify deep nesting is tracked correctly
        assert prov.value["level1"]["level2"]["level3"] == "child_value"
        assert prov.value["level1"]["level2"]["other"] == "root_other"
        assert prov.key_sources["level1.level2.level3"] == f"/{root_name}/{child_name}"
        assert prov.key_sources["level1.level2.other"] == f"/{root_name}"
