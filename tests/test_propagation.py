"""Tests for HRCP propagation modes - how values flow through the hierarchy."""

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


class TestPropagationModeEnum:
    """Test PropagationMode enumeration."""

    def test_propagation_modes_exist(self):
        """All expected propagation modes are defined."""
        assert PropagationMode.NONE is not None
        assert PropagationMode.INHERIT is not None
        assert PropagationMode.AGGREGATE is not None
        assert PropagationMode.MERGE is not None
        assert PropagationMode.REQUIRE_PATH is not None
        assert PropagationMode.COLLECT_ANCESTORS is not None

    def test_backward_compatibility_aliases(self):
        """Deprecated aliases still work for backward compatibility."""
        assert PropagationMode.DOWN is PropagationMode.INHERIT
        assert PropagationMode.UP is PropagationMode.AGGREGATE
        assert PropagationMode.MERGE_DOWN is PropagationMode.MERGE


class TestPropagationDown:
    """Test DOWN propagation - inheritance from ancestors."""

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, value=attr_value
    )
    def test_down_inherits_from_parent(self, root_name, child_name, key, value):
        """A child inherits values from its parent with DOWN propagation."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, value)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.DOWN)

        assert result == value

    @given(
        root_name=valid_name,
        names=st.lists(valid_name, min_size=2, max_size=4, unique=True),
        key=valid_name,
        value=attr_value,
    )
    def test_down_inherits_from_grandparent(self, root_name, names, key, value):
        """Values propagate down multiple levels."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, value)
        path = f"/{root_name}/" + "/".join(names)
        tree.create(path)

        leaf = tree.get(path)
        result = get_value(leaf, key, PropagationMode.DOWN)

        assert result == value

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        parent_val=st.integers(),
        child_val=st.integers(),
    )
    def test_down_local_value_overrides_parent(
        self, root_name, child_name, key, parent_val, child_val
    ):
        """A local value takes precedence over inherited value."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, parent_val)
        child = tree.create(f"/{root_name}/{child_name}", attributes={key: child_val})

        result = get_value(child, key, PropagationMode.DOWN)

        assert result == child_val

    @given(root_name=valid_name, child_name=valid_name, key=valid_name)
    def test_down_returns_none_if_not_found(self, root_name, child_name, key):
        """Returns None if attribute doesn't exist anywhere in chain."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.DOWN)

        assert result is None

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, default=attr_value
    )
    def test_down_with_default_value(self, root_name, child_name, key, default):
        """Returns default if attribute not found."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.DOWN, default=default)

        assert result == default


class TestPropagationUp:
    """Test UP propagation - aggregation from descendants."""

    @given(
        root_name=valid_name,
        child_names=st.lists(valid_name, min_size=2, max_size=4, unique=True),
        key=valid_name,
        values=st.lists(st.integers(), min_size=2, max_size=4),
    )
    def test_up_collects_from_children(self, root_name, child_names, key, values):
        """UP aggregates values from immediate children."""
        tree = ResourceTree(root_name=root_name)
        used_values = []
        for name, val in zip(child_names, values, strict=False):
            tree.create(f"/{root_name}/{name}", attributes={key: val})
            used_values.append(val)

        result = get_value(tree.root, key, PropagationMode.UP)

        assert sorted(result) == sorted(used_values)

    @given(
        root_name=valid_name,
        region1=valid_name,
        region2=valid_name,
        key=valid_name,
        val1=st.integers(),
        val2=st.integers(),
    )
    def test_up_collects_from_all_descendants(
        self, root_name, region1, region2, key, val1, val2
    ):
        """UP aggregates values from all descendants, not just children."""
        if region1 == region2:
            region2 = region2 + "2"
        tree = ResourceTree(root_name=root_name)
        tree.create(f"/{root_name}/{region1}/server", attributes={key: val1})
        tree.create(f"/{root_name}/{region2}/server", attributes={key: val2})

        result = get_value(tree.root, key, PropagationMode.UP)

        assert sorted(result) == sorted([val1, val2])

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        root_val=st.integers(),
        child_val=st.integers(),
    )
    def test_up_includes_local_value(
        self, root_name, child_name, key, root_val, child_val
    ):
        """UP includes the resource's own value if present."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, root_val)
        tree.create(f"/{root_name}/{child_name}", attributes={key: child_val})

        result = get_value(tree.root, key, PropagationMode.UP)

        assert sorted(result) == sorted([child_val, root_val])

    @given(root_name=valid_name, child_name=valid_name, key=valid_name)
    def test_up_returns_empty_list_if_not_found(self, root_name, child_name, key):
        """Returns empty list if attribute doesn't exist anywhere."""
        tree = ResourceTree(root_name=root_name)
        tree.create(f"/{root_name}/{child_name}")

        result = get_value(tree.root, key, PropagationMode.UP)

        assert result == []

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, value=st.integers()
    )
    def test_up_from_leaf_returns_own_value_as_list(
        self, root_name, child_name, key, value
    ):
        """A leaf node's UP aggregation is just its own value."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}", attributes={key: value})

        result = get_value(child, key, PropagationMode.UP)

        assert result == [value]


class TestPropagationMergeDown:
    """Test MERGE_DOWN propagation - deep merge of dicts from ancestors."""

    @given(
        root_name=valid_name,
        child_name=valid_name,
        k1=valid_name,
        k2=valid_name,
        k3=valid_name,
        v1=st.integers(),
        v2=st.integers(),
        v3=st.integers(),
    )
    def test_merge_down_combines_dicts(
        self, root_name, child_name, k1, k2, k3, v1, v2, v3
    ):
        """MERGE_DOWN deep-merges dict values from ancestors."""
        # Ensure distinct keys
        if k1 == k2:
            k2 = k2 + "2"
        if k3 in (k2, k1):
            k3 = k3 + "3"
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute("config", {k1: v1, k2: v2})
        child = tree.create(
            f"/{root_name}/{child_name}", attributes={"config": {k2: v3, k3: v3}}
        )

        result = get_value(child, "config", PropagationMode.MERGE_DOWN)

        # Parent's k1 preserved, child's k2 overrides, child adds k3
        assert result == {k1: v1, k2: v3, k3: v3}

    @given(root_name=valid_name, mid_name=valid_name, leaf_name=valid_name)
    def test_merge_down_multiple_levels(self, root_name, mid_name, leaf_name):
        """MERGE_DOWN merges across multiple ancestor levels."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute("config", {"level": "root", "x": 1})
        tree.create(
            f"/{root_name}/{mid_name}",
            attributes={"config": {"level": "region", "y": 2}},
        )
        tree.create(
            f"/{root_name}/{mid_name}/{leaf_name}",
            attributes={"config": {"level": "server", "z": 3}},
        )

        server = tree.get(f"/{root_name}/{mid_name}/{leaf_name}")
        result = get_value(server, "config", PropagationMode.MERGE_DOWN)

        assert result == {"level": "server", "x": 1, "y": 2, "z": 3}

    @given(root_name=valid_name, child_name=valid_name)
    def test_merge_down_nested_dicts(self, root_name, child_name):
        """MERGE_DOWN recursively merges nested dictionaries."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(
            "settings",
            {"logging": {"level": "INFO", "format": "json"}, "timeout": 30},
        )
        child = tree.create(
            f"/{root_name}/{child_name}",
            attributes={"settings": {"logging": {"level": "DEBUG"}, "port": 8080}},
        )

        result = get_value(child, "settings", PropagationMode.MERGE_DOWN)

        assert result == {
            "logging": {"level": "DEBUG", "format": "json"},
            "timeout": 30,
            "port": 8080,
        }

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, value=st.integers()
    )
    def test_merge_down_non_dict_uses_down_behavior(
        self, root_name, child_name, key, value
    ):
        """For non-dict values, MERGE_DOWN falls back to DOWN behavior."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, value)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.MERGE_DOWN)

        assert result == value

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        child_val=attr_value,
    )
    def test_merge_down_child_non_dict_overrides_parent_dict(
        self, root_name, child_name, key, child_val
    ):
        """If child has non-dict, it replaces parent's dict entirely."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, {"complex": "dict"})
        child = tree.create(f"/{root_name}/{child_name}", attributes={key: child_val})

        result = get_value(child, key, PropagationMode.MERGE_DOWN)

        assert result == child_val


class TestPropagationNone:
    """Test NONE propagation - no inheritance, only local values."""

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        parent_val=attr_value,
        child_val=attr_value,
    )
    def test_none_returns_local_value_only(
        self, root_name, child_name, key, parent_val, child_val
    ):
        """NONE mode returns only the resource's own value."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, parent_val)
        child = tree.create(f"/{root_name}/{child_name}", attributes={key: child_val})

        result = get_value(child, key, PropagationMode.NONE)

        assert result == child_val

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        parent_val=attr_value,
    )
    def test_none_ignores_parent_value(self, root_name, child_name, key, parent_val):
        """NONE mode ignores parent values."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, parent_val)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.NONE)

        assert result is None

    @given(
        root_name=valid_name,
        child_name=valid_name,
        key=valid_name,
        parent_val=attr_value,
        default=attr_value,
    )
    def test_none_with_default(self, root_name, child_name, key, parent_val, default):
        """NONE mode respects default when no local value."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, parent_val)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.NONE, default=default)

        assert result == default


class TestPropagationRequirePath:
    """Test REQUIRE_PATH propagation - all ancestors must have truthy value."""

    def test_require_path_all_truthy(self):
        """Returns value when all ancestors have truthy values."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)
        tree.create("/org/team", attributes={"enabled": True})
        account = tree.create("/org/team/account", attributes={"enabled": True})

        result = get_value(account, "enabled", PropagationMode.REQUIRE_PATH)

        assert result is True

    def test_require_path_local_missing(self):
        """Returns None if local value is missing."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)
        tree.create("/org/team", attributes={"enabled": True})
        account = tree.create("/org/team/account")  # No enabled attribute

        result = get_value(account, "enabled", PropagationMode.REQUIRE_PATH)

        assert result is None

    def test_require_path_local_falsy(self):
        """Returns None if local value is falsy."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)
        tree.create("/org/team", attributes={"enabled": True})
        account = tree.create("/org/team/account", attributes={"enabled": False})

        result = get_value(account, "enabled", PropagationMode.REQUIRE_PATH)

        assert result is None

    def test_require_path_ancestor_missing(self):
        """Returns None if any ancestor is missing the value."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)
        tree.create("/org/team")  # No enabled attribute
        account = tree.create("/org/team/account", attributes={"enabled": True})

        result = get_value(account, "enabled", PropagationMode.REQUIRE_PATH)

        assert result is None

    def test_require_path_ancestor_falsy(self):
        """Returns None if any ancestor has falsy value."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", False)  # Falsy at root
        tree.create("/org/team", attributes={"enabled": True})
        account = tree.create("/org/team/account", attributes={"enabled": True})

        result = get_value(account, "enabled", PropagationMode.REQUIRE_PATH)

        assert result is None

    def test_require_path_root_only(self):
        """Works correctly when resource is root."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)

        result = get_value(tree.root, "enabled", PropagationMode.REQUIRE_PATH)

        assert result is True

    def test_require_path_provenance(self):
        """Provenance tracks all contributing paths."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)
        tree.create("/org/team", attributes={"enabled": True})
        account = tree.create("/org/team/account", attributes={"enabled": True})

        prov = get_value(
            account, "enabled", PropagationMode.REQUIRE_PATH, with_provenance=True
        )

        assert prov is not None
        assert prov.value is True
        assert prov.source_path == "/org/team/account"
        assert prov.contributing_paths == ["/org", "/org/team", "/org/team/account"]


class TestPropagationCollectAncestors:
    """Test COLLECT_ANCESTORS propagation - collect values from self to root."""

    def test_collect_ancestors_all_present(self):
        """Collects all values from self to root."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("level", "org")
        tree.create("/org/team", attributes={"level": "team"})
        account = tree.create("/org/team/account", attributes={"level": "account"})

        result = get_value(account, "level", PropagationMode.COLLECT_ANCESTORS)

        # Values collected from account up to root
        assert result == ["account", "team", "org"]

    def test_collect_ancestors_some_missing(self):
        """Skips nodes without the attribute."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("level", "org")
        tree.create("/org/team")  # No level attribute
        account = tree.create("/org/team/account", attributes={"level": "account"})

        result = get_value(account, "level", PropagationMode.COLLECT_ANCESTORS)

        assert result == ["account", "org"]

    def test_collect_ancestors_none_present(self):
        """Returns empty list if no ancestor has the value."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team")
        account = tree.create("/org/team/account")

        result = get_value(account, "level", PropagationMode.COLLECT_ANCESTORS)

        assert result == []

    def test_collect_ancestors_root_only(self):
        """Works correctly when resource is root."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("level", "org")

        result = get_value(tree.root, "level", PropagationMode.COLLECT_ANCESTORS)

        assert result == ["org"]

    def test_collect_ancestors_for_all_check(self):
        """Can be used with all() for REQUIRE_PATH-like behavior."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)
        tree.create("/org/team", attributes={"enabled": True})
        account = tree.create("/org/team/account", attributes={"enabled": True})

        values = get_value(account, "enabled", PropagationMode.COLLECT_ANCESTORS)

        assert all(values) is True

    def test_collect_ancestors_for_any_check(self):
        """Can be used with any() for inheritance-like behavior."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("enabled", True)
        tree.create("/org/team", attributes={"enabled": False})
        account = tree.create("/org/team/account", attributes={"enabled": False})

        values = get_value(account, "enabled", PropagationMode.COLLECT_ANCESTORS)

        assert any(values) is True

    def test_collect_ancestors_provenance(self):
        """Provenance tracks all contributing paths."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("level", "org")
        tree.create("/org/team", attributes={"level": "team"})
        account = tree.create("/org/team/account", attributes={"level": "account"})

        prov = get_value(
            account, "level", PropagationMode.COLLECT_ANCESTORS, with_provenance=True
        )

        assert prov.value == ["account", "team", "org"]
        assert prov.source_path == "/org/team/account"
        assert prov.contributing_paths == ["/org/team/account", "/org/team", "/org"]


class TestGetValueCombined:
    """Test the combined get_value function with optional provenance."""

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, value=attr_value
    )
    def test_get_value_returns_value_by_default(
        self, root_name, child_name, key, value
    ):
        """get_value returns just the value when with_provenance=False."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, value)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.INHERIT)

        assert result == value

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, value=attr_value
    )
    def test_get_value_returns_provenance_when_requested(
        self, root_name, child_name, key, value
    ):
        """get_value returns Provenance when with_provenance=True."""
        tree = ResourceTree(root_name=root_name)
        tree.root.set_attribute(key, value)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.DOWN, with_provenance=True)

        assert isinstance(result, Provenance)
        assert result.value == value
        assert result.source_path == f"/{root_name}"

    @given(
        root_name=valid_name, child_name=valid_name, key=valid_name, default=attr_value
    )
    def test_get_value_respects_default(self, root_name, child_name, key, default):
        """get_value returns default when value not found."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.DOWN, default=default)

        assert result == default

    @given(root_name=valid_name, child_name=valid_name, key=valid_name)
    def test_get_value_provenance_none_when_not_found(self, root_name, child_name, key):
        """get_value returns None provenance when value not found and provenance requested."""
        tree = ResourceTree(root_name=root_name)
        child = tree.create(f"/{root_name}/{child_name}")

        result = get_value(child, key, PropagationMode.DOWN, with_provenance=True)

        assert result is None
