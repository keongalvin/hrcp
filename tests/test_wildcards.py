"""Tests for HRCP wildcard query system - pattern-based resource access."""

from hypothesis import given
from hypothesis import strategies as st

from hrcp.core import ResourceTree
from hrcp.propagation import PropagationMode

# Strategy for valid resource names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)


class TestSingleWildcard:
    """Test single wildcard (*) matching."""

    @given(root=valid_name, region1=valid_name, region2=valid_name, region3=valid_name)
    def test_wildcard_matches_any_single_segment(self, root, region1, region2, region3):
        """Single * matches any single path segment."""
        # Ensure unique region names
        regions = [region1, region2 + "2" if region2 == region1 else region2]
        region3 = region3 + "3" if region3 in regions else region3
        regions.append(region3)

        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{regions[0]}/server")
        tree.create(f"/{root}/{regions[1]}/server")
        tree.create(f"/{root}/{regions[2]}/database")

        results = tree.query(f"/{root}/*/server")

        paths = [r.path for r in results]
        assert f"/{root}/{regions[0]}/server" in paths
        assert f"/{root}/{regions[1]}/server" in paths
        assert f"/{root}/{regions[2]}/database" not in paths
        assert len(results) == 2

    @given(root=valid_name, loc1=valid_name, loc2=valid_name, dc1=valid_name, dc2=valid_name)
    def test_wildcard_at_different_positions(self, root, loc1, loc2, dc1, dc2):
        """Wildcard can appear at different path positions."""
        if loc1 == loc2:
            loc2 = loc2 + "2"
        if dc1 == dc2:
            dc2 = dc2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{loc1}/{dc1}/host1")
        tree.create(f"/{root}/{loc1}/{dc2}/host1")
        tree.create(f"/{root}/{loc2}/{dc1}/host1")

        # Wildcard in middle
        results = tree.query(f"/{root}/{loc1}/*/host1")
        assert len(results) == 2

        # Wildcard at start
        results = tree.query(f"/{root}/*/{dc1}/host1")
        assert len(results) == 2

    @given(root=valid_name, region=valid_name, hosts=st.lists(valid_name, min_size=2, max_size=4, unique=True))
    def test_wildcard_at_end(self, root, region, hosts):
        """Wildcard at end matches any children."""
        tree = ResourceTree(root_name=root)
        for host in hosts:
            tree.create(f"/{root}/{region}/{host}")

        results = tree.query(f"/{root}/{region}/*")

        assert len(results) == len(hosts)

    @given(root=valid_name, locs=st.lists(valid_name, min_size=2, max_size=3, unique=True), dcs=st.lists(valid_name, min_size=2, max_size=3, unique=True))
    def test_multiple_single_wildcards(self, root, locs, dcs):
        """Multiple single wildcards in one pattern."""
        tree = ResourceTree(root_name=root)
        for loc in locs:
            for dc in dcs:
                tree.create(f"/{root}/{loc}/{dc}/host")

        results = tree.query(f"/{root}/*/*/host")

        assert len(results) == len(locs) * len(dcs)

    @given(root=valid_name, region=valid_name, child=valid_name)
    def test_no_matches_returns_empty(self, root, region, child):
        """Pattern with no matches returns empty list."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{region}/{child}")

        results = tree.query(f"/{root}/*/nonexistent")

        assert results == []


class TestDoubleWildcard:
    """Test double wildcard (**) for recursive matching."""

    @given(root=valid_name)
    def test_double_wildcard_matches_any_depth(self, root):
        """Double ** matches paths at any depth."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/host")
        tree.create(f"/{root}/region/host")
        tree.create(f"/{root}/region/dc/host")
        tree.create(f"/{root}/region/dc/rack/host")

        results = tree.query(f"/{root}/**/host")

        assert len(results) == 4

    @given(root=valid_name, names=st.lists(valid_name, min_size=1, max_size=3, unique=True))
    def test_double_wildcard_at_end(self, root, names):
        """Double ** at end matches all descendants."""
        tree = ResourceTree(root_name=root)
        path = f"/{root}"
        for name in names:
            path = f"{path}/{name}"
            tree.create(path)

        results = tree.query(f"/{root}/**")

        # Should match all descendants of root
        assert len(results) >= len(names)

    @given(root=valid_name, mid1=valid_name, mid2=valid_name)
    def test_double_wildcard_in_middle(self, root, mid1, mid2):
        """Double ** in middle of pattern."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{mid1}/dc/rack/host/config")
        tree.create(f"/{root}/{mid2}/host/config")

        results = tree.query(f"/{root}/**/config")

        assert len(results) == 2

    @given(root=valid_name)
    def test_double_wildcard_matches_zero_segments(self, root):
        """Double ** can match zero intermediate segments."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/host")  # Direct child

        results = tree.query(f"/{root}/**/host")

        paths = [r.path for r in results]
        assert f"/{root}/host" in paths


class TestMixedWildcards:
    """Test combining single and double wildcards."""

    @given(root=valid_name, loc1=valid_name, loc2=valid_name, dc=valid_name)
    def test_single_and_double_combined(self, root, loc1, loc2, dc):
        """Combine * and ** in same pattern."""
        if loc1 == loc2:
            loc2 = loc2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{loc1}/{dc}/server")
        tree.create(f"/{root}/{loc1}/{dc}/rack/server")
        tree.create(f"/{root}/{loc2}/dc2/server")

        results = tree.query(f"/{root}/{loc1}/**/server")

        paths = [r.path for r in results]
        assert f"/{root}/{loc1}/{dc}/server" in paths
        assert f"/{root}/{loc1}/{dc}/rack/server" in paths
        assert f"/{root}/{loc2}/dc2/server" not in paths


class TestQueryExactPath:
    """Test exact path queries (no wildcards)."""

    @given(root=valid_name, region=valid_name, child=valid_name)
    def test_exact_path_returns_single_resource(self, root, region, child):
        """Exact path returns single-element list."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{region}/{child}")

        results = tree.query(f"/{root}/{region}/{child}")

        assert len(results) == 1
        assert results[0].path == f"/{root}/{region}/{child}"

    @given(root=valid_name, fake=valid_name)
    def test_exact_path_not_found_returns_empty(self, root, fake):
        """Non-existent exact path returns empty list."""
        tree = ResourceTree(root_name=root)

        results = tree.query(f"/{root}/{fake}")

        assert results == []


class TestQueryValues:
    """Test querying attribute values across multiple resources."""

    @given(root=valid_name, child1=valid_name, child2=valid_name, key=valid_name, parent_val=st.text(max_size=20))
    def test_query_values_with_down_propagation(self, root, child1, child2, key, parent_val):
        """Get values from matching resources with DOWN propagation."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.root.set_attribute(key, parent_val)
        tree.create(f"/{root}/{child1}")
        tree.create(f"/{root}/{child2}")

        values = tree.query_values(f"/{root}/*", key, PropagationMode.DOWN)

        # Both children inherit value from parent
        assert values == [parent_val, parent_val]

    @given(root=valid_name, child1=valid_name, child2=valid_name, key=valid_name, val1=st.integers(), val2=st.integers())
    def test_query_values_returns_local_values(self, root, child1, child2, key, val1, val2):
        """Get local values from matching resources."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child1}", attributes={key: val1})
        tree.create(f"/{root}/{child2}", attributes={key: val2})

        values = tree.query_values(f"/{root}/*", key, PropagationMode.NONE)

        assert sorted(values) == sorted([val1, val2])

    @given(root=valid_name, child1=valid_name, child2=valid_name, key=valid_name, val=st.integers())
    def test_query_values_skips_missing(self, root, child1, child2, key, val):
        """Missing values are not included in results."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child1}", attributes={key: val})
        tree.create(f"/{root}/{child2}")  # No attribute

        values = tree.query_values(f"/{root}/*", key, PropagationMode.NONE)

        assert values == [val]
