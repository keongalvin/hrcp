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

    @given(
        root=valid_name,
        loc1=valid_name,
        loc2=valid_name,
        dc1=valid_name,
        dc2=valid_name,
    )
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

    @given(
        root=valid_name,
        region=valid_name,
        hosts=st.lists(valid_name, min_size=2, max_size=4, unique=True),
    )
    def test_wildcard_at_end(self, root, region, hosts):
        """Wildcard at end matches any children."""
        tree = ResourceTree(root_name=root)
        for host in hosts:
            tree.create(f"/{root}/{region}/{host}")

        results = tree.query(f"/{root}/{region}/*")

        assert len(results) == len(hosts)

    @given(
        root=valid_name,
        locs=st.lists(valid_name, min_size=2, max_size=3, unique=True),
        dcs=st.lists(valid_name, min_size=2, max_size=3, unique=True),
    )
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

    @given(root=valid_name, region=valid_name)
    def test_wildcard_within_segment(self, root, region):
        """Wildcard within segment matches partial names (e.g., server*)."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{region}/server1")
        tree.create(f"/{root}/{region}/server2")
        tree.create(f"/{root}/{region}/database")

        results = tree.query(f"/{root}/{region}/server*")

        paths = [r.path for r in results]
        assert f"/{root}/{region}/server1" in paths
        assert f"/{root}/{region}/server2" in paths
        assert f"/{root}/{region}/database" not in paths
        assert len(results) == 2


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

    @given(
        root=valid_name, names=st.lists(valid_name, min_size=1, max_size=3, unique=True)
    )
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

    @given(
        root=valid_name,
        child1=valid_name,
        child2=valid_name,
        key=valid_name,
        parent_val=st.text(max_size=20),
    )
    def test_query_values_with_down_propagation(
        self, root, child1, child2, key, parent_val
    ):
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

    @given(
        root=valid_name,
        child1=valid_name,
        child2=valid_name,
        key=valid_name,
        val1=st.integers(),
        val2=st.integers(),
    )
    def test_query_values_returns_local_values(
        self, root, child1, child2, key, val1, val2
    ):
        """Get local values from matching resources."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child1}", attributes={key: val1})
        tree.create(f"/{root}/{child2}", attributes={key: val2})

        values = tree.query_values(f"/{root}/*", key, PropagationMode.NONE)

        assert sorted(values) == sorted([val1, val2])

    @given(
        root=valid_name,
        child1=valid_name,
        child2=valid_name,
        key=valid_name,
        val=st.integers(),
    )
    def test_query_values_skips_missing(self, root, child1, child2, key, val):
        """Missing values are not included in results."""
        if child1 == child2:
            child2 = child2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child1}", attributes={key: val})
        tree.create(f"/{root}/{child2}")  # No attribute

        values = tree.query_values(f"/{root}/*", key, PropagationMode.NONE)

        assert values == [val]

    @given(
        root=valid_name,
        region1=valid_name,
        region2=valid_name,
        key=valid_name,
        val1=st.integers(),
        val2=st.integers(),
    )
    def test_query_values_with_up_propagation(
        self, root, region1, region2, key, val1, val2
    ):
        """query_values with UP mode aggregates and extends results."""
        if region1 == region2:
            region2 = region2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{region1}/child1", attributes={key: val1})
        tree.create(f"/{root}/{region2}/child2", attributes={key: val2})

        # Query both regions with UP mode - each region collects from its descendants
        values = tree.query_values(f"/{root}/*", key, PropagationMode.UP)

        # UP returns lists, query_values extends them
        assert sorted(values) == sorted([val1, val2])


class TestWildcardEdgeCases:
    """Test edge cases in wildcard pattern matching."""

    @given(root=valid_name)
    def test_root_only_pattern_matches_root(self, root):
        """Pattern '/' or '/{root}' should match only the root."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/child")

        results = tree.query(f"/{root}")

        assert len(results) == 1
        assert results[0].path == f"/{root}"

    @given(root=valid_name, child=valid_name)
    def test_double_wildcard_matches_root_and_descendants(self, root, child):
        """Pattern '/{root}/**' should match root and all descendants."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")

        results = tree.query(f"/{root}/**")

        paths = [r.path for r in results]
        # Should include the child (and possibly root depending on semantics)
        assert f"/{root}/{child}" in paths

    @given(root=valid_name, child=valid_name)
    def test_trailing_slash_ignored(self, root, child):
        """Trailing slash should not affect matching."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")

        results_no_slash = tree.query(f"/{root}/{child}")
        results_with_slash = tree.query(f"/{root}/{child}/")

        assert len(results_no_slash) == len(results_with_slash)
        assert results_no_slash[0].path == results_with_slash[0].path


class TestSpecialCharactersInPaths:
    """Test paths containing regex metacharacters."""

    @given(root=valid_name)
    def test_dot_in_path_literal_match(self, root):
        """Dots in paths should match literally, not as regex wildcard."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/server.prod")
        tree.create(f"/{root}/serverXprod")  # Would match if . is regex

        results = tree.query(f"/{root}/server.prod")

        assert len(results) == 1
        assert results[0].path == f"/{root}/server.prod"

    @given(root=valid_name)
    def test_brackets_in_path(self, root):
        """Brackets should match literally."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/host[0]")
        tree.create(f"/{root}/host1")

        results = tree.query(f"/{root}/host[0]")

        assert len(results) == 1
        assert results[0].path == f"/{root}/host[0]"

    @given(root=valid_name)
    def test_parentheses_in_path(self, root):
        """Parentheses should match literally."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/group(1)")

        results = tree.query(f"/{root}/group(1)")

        assert len(results) == 1
        assert results[0].path == f"/{root}/group(1)"

    @given(root=valid_name)
    def test_plus_in_path(self, root):
        """Plus signs should match literally."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/c++")
        tree.create(f"/{root}/ccc")  # Would match if + is regex

        results = tree.query(f"/{root}/c++")

        assert len(results) == 1
        assert results[0].path == f"/{root}/c++"

    @given(root=valid_name)
    def test_caret_and_dollar_in_path(self, root):
        """Caret and dollar should match literally."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/$var")
        tree.create(f"/{root}/^start")

        results_dollar = tree.query(f"/{root}/$var")
        results_caret = tree.query(f"/{root}/^start")

        assert len(results_dollar) == 1
        assert len(results_caret) == 1


class TestMultipleWildcardsInSegment:
    """Test multiple wildcards within a single path segment."""

    @given(root=valid_name)
    def test_wildcard_prefix(self, root):
        """Wildcard at start of segment: *server."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/webserver")
        tree.create(f"/{root}/appserver")
        tree.create(f"/{root}/database")

        results = tree.query(f"/{root}/*server")

        paths = [r.path for r in results]
        assert f"/{root}/webserver" in paths
        assert f"/{root}/appserver" in paths
        assert f"/{root}/database" not in paths
        assert len(results) == 2

    @given(root=valid_name)
    def test_wildcard_middle_of_segment(self, root):
        """Wildcard in middle: host*1."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/host01")
        tree.create(f"/{root}/hosting1")
        tree.create(f"/{root}/host02")

        results = tree.query(f"/{root}/host*1")

        paths = [r.path for r in results]
        assert f"/{root}/host01" in paths
        assert f"/{root}/hosting1" in paths
        assert f"/{root}/host02" not in paths

    @given(root=valid_name)
    def test_multiple_wildcards_in_segment(self, root):
        """Multiple wildcards in one segment: s*v*r."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/server")
        tree.create(f"/{root}/saver")
        tree.create(f"/{root}/sliver")
        tree.create(f"/{root}/database")

        results = tree.query(f"/{root}/s*v*r")

        paths = [r.path for r in results]
        assert f"/{root}/server" in paths
        assert f"/{root}/saver" in paths
        assert f"/{root}/sliver" in paths
        assert f"/{root}/database" not in paths


class TestComplexWildcardCombinations:
    """Test complex combinations of wildcards."""

    @given(root=valid_name, mid=valid_name)
    def test_double_wildcard_followed_by_single(self, root, mid):
        """Pattern /**/* should match any path with at least one segment after root."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{mid}")
        tree.create(f"/{root}/{mid}/child")
        tree.create(f"/{root}/{mid}/child/grandchild")

        results = tree.query(f"/{root}/**/*")

        # Should match all descendants (each has at least one segment)
        assert len(results) >= 3

    @given(root=valid_name, a=valid_name, b=valid_name)
    def test_multiple_double_wildcards(self, root, a, b):
        """Pattern /**/a/**/b with double wildcards at multiple positions."""
        if a == b:
            b = b + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{a}/{b}")
        tree.create(f"/{root}/x/{a}/y/{b}")
        tree.create(f"/{root}/{a}/mid/{b}")
        tree.create(f"/{root}/{a}/other")  # No b at end

        results = tree.query(f"/{root}/**/{a}/**/{b}")

        paths = [r.path for r in results]
        assert f"/{root}/{a}/{b}" in paths
        assert f"/{root}/x/{a}/y/{b}" in paths
        assert f"/{root}/{a}/mid/{b}" in paths
        assert f"/{root}/{a}/other" not in paths

    @given(root=valid_name, child=valid_name)
    def test_single_wildcard_then_double_wildcard(self, root, child):
        """Pattern /root/*/**: single then double wildcard."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")
        tree.create(f"/{root}/{child}/a")
        tree.create(f"/{root}/{child}/a/b")

        results = tree.query(f"/{root}/*/**")

        # Should match child and all its descendants
        paths = [r.path for r in results]
        assert f"/{root}/{child}" in paths
        assert f"/{root}/{child}/a" in paths
        assert f"/{root}/{child}/a/b" in paths

    @given(root=valid_name)
    def test_consecutive_single_wildcards(self, root):
        """Pattern /*/*/* with consecutive single wildcards."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/a/b")
        tree.create(f"/{root}/a/b/c")
        tree.create(f"/{root}/a/b/c/d")

        results = tree.query(f"/{root}/*/*/*")

        # Should match exactly 3 levels deep
        paths = [r.path for r in results]
        assert f"/{root}/a/b/c" in paths
        assert f"/{root}/a/b" not in paths
        assert f"/{root}/a/b/c/d" not in paths


class TestMalformedPatterns:
    """Test handling of malformed or unusual patterns."""

    @given(root=valid_name, child=valid_name)
    def test_double_slashes_in_pattern(self, root, child):
        """Double slashes should be handled gracefully."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")

        # Pattern with double slash - should either normalize or match nothing
        results = tree.query(f"/{root}//{child}")

        # Should either match the path or return empty, not raise
        assert isinstance(results, list)

    @given(root=valid_name, child=valid_name)
    def test_pattern_without_leading_slash(self, root, child):
        """Pattern without leading slash should still work."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")

        results = tree.query(f"{root}/{child}")

        # Should match the path (normalized)
        assert len(results) == 1
        assert results[0].path == f"/{root}/{child}"

    @given(root=valid_name)
    def test_empty_pattern(self, root):
        """Empty pattern should return empty or match root."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/child")

        results = tree.query("")

        # Empty pattern - should return empty list or just root
        assert isinstance(results, list)

    @given(root=valid_name, child=valid_name)
    def test_only_wildcards_pattern(self, root, child):
        """Pattern of only wildcards: /*."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{child}")

        results = tree.query("/*")

        # Should match the root
        paths = [r.path for r in results]
        assert f"/{root}" in paths


class TestPatternToRegexCorrectness:
    """Test that pattern_to_regex produces correct regex strings."""

    def test_no_duplicate_anchors(self):
        """Recursive patterns should not produce duplicate $ anchors."""
        from hrcp.wildcards import pattern_to_regex

        # Multiple ** in pattern
        regex = pattern_to_regex("/**/a/**/b/**/c")

        # Should have exactly one $ at the end
        assert regex.endswith("$")
        assert not regex.endswith("$$")

    def test_deeply_nested_double_wildcards(self):
        """Deep nesting of ** should not cause exponential anchor growth."""
        from hrcp.wildcards import pattern_to_regex

        regex = pattern_to_regex("/**/a/**/b/**/c/**/d/**/e/**/f")

        # Count $ signs - should be exactly 1
        dollar_count = regex.count("$")
        assert dollar_count == 1, f"Expected 1 $, got {dollar_count}: {regex}"

    @given(
        root=valid_name,
        segments=st.lists(valid_name, min_size=1, max_size=5, unique=True),
    )
    def test_complex_pattern_matches_correctly(self, root, segments):
        """Complex patterns with multiple ** should match correct paths."""
        from hrcp.wildcards import match_pattern

        # Build a path and pattern with ** between each segment
        path = f"/{root}/" + "/".join(segments)
        pattern = f"/{root}/**/" + "/**/".join(segments)

        # Should match
        assert match_pattern(path, pattern)

    @given(root=valid_name)
    def test_three_consecutive_double_wildcards(self, root):
        """Three consecutive ** should work correctly."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/a/b/c")

        results = tree.query(f"/{root}/**/**/**/c")

        paths = [r.path for r in results]
        assert f"/{root}/a/b/c" in paths
