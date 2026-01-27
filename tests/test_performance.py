"""Performance tests for HRCP.

These tests verify that HRCP operations complete within acceptable time bounds.
They serve as regression tests to catch performance degradation.

Note: Each test creates fresh data structures to avoid any caching effects.
Fixtures use function scope to ensure isolation between tests.
"""

import gc
import time

import pytest

from hrcp import PropagationMode
from hrcp import ResourceTree
from hrcp import get_value


def _timed_iterations(func, iterations: int) -> float:
    """Run iterations with GC disabled for consistent timing."""
    gc.collect()
    gc.disable()
    try:
        start = time.perf_counter()
        for _ in range(iterations):
            func()
        return time.perf_counter() - start
    finally:
        gc.enable()


class TestTreeCreationPerformance:
    """Performance tests for tree creation operations.

    Note: Creation tests inherently use fresh trees each time, so no caching issues.
    """

    def test_create_wide_tree(self):
        """Creating a tree with 1000 children should complete quickly."""
        gc.collect()
        gc.disable()
        try:
            tree = ResourceTree(root_name="root")
            start = time.perf_counter()
            for i in range(1000):
                tree.create(f"/root/child_{i}", attributes={"index": i})
            elapsed = time.perf_counter() - start
        finally:
            gc.enable()

        assert len(tree) == 1001  # root + 1000 children
        assert elapsed < 1.0, (
            f"Creating 1000 children took {elapsed:.2f}s (expected < 1s)"
        )

    def test_create_deep_tree(self):
        """Creating a tree with depth 100 should complete quickly."""
        gc.collect()
        gc.disable()
        try:
            tree = ResourceTree(root_name="root")
            start = time.perf_counter()
            path = "/root"
            for i in range(100):
                path = f"{path}/level_{i}"
                tree.create(path, attributes={"depth": i})
            elapsed = time.perf_counter() - start
        finally:
            gc.enable()

        assert len(tree) == 101  # root + 100 levels
        assert elapsed < 1.0, (
            f"Creating depth-100 tree took {elapsed:.2f}s (expected < 1s)"
        )

    def test_create_balanced_tree(self):
        """Creating a balanced tree with ~1000 nodes should complete quickly."""
        gc.collect()
        gc.disable()
        try:
            tree = ResourceTree(root_name="root")
            start = time.perf_counter()
            # Create 10 children, each with 10 grandchildren, each with 10 great-grandchildren
            for i in range(10):
                tree.create(f"/root/a_{i}")
                for j in range(10):
                    tree.create(f"/root/a_{i}/b_{j}")
                    for k in range(10):
                        tree.create(
                            f"/root/a_{i}/b_{j}/c_{k}",
                            attributes={"value": i * 100 + j * 10 + k},
                        )
            elapsed = time.perf_counter() - start
        finally:
            gc.enable()

        assert len(tree) == 1111  # 1 + 10 + 100 + 1000
        assert elapsed < 2.0, (
            f"Creating 1111-node tree took {elapsed:.2f}s (expected < 2s)"
        )


class TestLookupPerformance:
    """Performance tests for resource lookup operations.

    Note: Lookups use different paths each iteration to avoid any path caching.
    """

    @pytest.fixture
    def large_tree(self):
        """Create a fresh tree with 1000+ nodes for lookup tests."""
        tree = ResourceTree(root_name="root")
        for i in range(10):
            tree.create(f"/root/a_{i}")
            for j in range(10):
                tree.create(f"/root/a_{i}/b_{j}")
                for k in range(10):
                    tree.create(
                        f"/root/a_{i}/b_{j}/c_{k}",
                        attributes={"value": i * 100 + j * 10 + k},
                    )
        return tree

    def test_get_by_path(self, large_tree):
        """Looking up resources by path should be fast."""
        # Use varying paths to avoid any potential caching
        paths = [f"/root/a_{i % 10}/b_{(i // 10) % 10}/c_{i % 10}" for i in range(1000)]

        elapsed = _timed_iterations(
            lambda: large_tree.get(paths[0]),  # Fresh lookup each time
            iterations=1,
        )
        # Now do the real benchmark with varying paths
        gc.collect()
        gc.disable()
        try:
            start = time.perf_counter()
            for path in paths:
                resource = large_tree.get(path)
            elapsed = time.perf_counter() - start
        finally:
            gc.enable()

        assert resource is not None
        assert elapsed < 0.1, f"1000 path lookups took {elapsed:.2f}s (expected < 0.1s)"

    def test_walk_tree(self, large_tree):
        """Walking the entire tree should complete quickly."""
        elapsed = _timed_iterations(
            lambda: sum(1 for _ in large_tree.walk()),
            iterations=1,
        )
        # Count after timing
        count = sum(1 for _ in large_tree.walk())

        assert count == 1111
        assert elapsed < 0.1, (
            f"Walking 1111 nodes took {elapsed:.2f}s (expected < 0.1s)"
        )


class TestPropagationPerformance:
    """Performance tests for value propagation operations."""

    @pytest.fixture
    def deep_tree(self):
        """Create a deep tree for propagation tests."""
        tree = ResourceTree(root_name="root")
        tree.root.set_attribute("inherited", "from_root")
        tree.root.set_attribute("config", {"a": 1, "b": 2, "c": 3})

        path = "/root"
        for i in range(50):
            path = f"{path}/level_{i}"
            tree.create(path, attributes={"depth": i})

        return tree

    def test_down_propagation_deep(self, deep_tree):
        """DOWN propagation through 50 levels should be fast."""
        # Get deepest node
        current = deep_tree.root
        for i in range(50):
            current = current.get_child(f"level_{i}")

        start = time.perf_counter()
        for _ in range(1000):
            value = get_value(current, "inherited", PropagationMode.DOWN)
        elapsed = time.perf_counter() - start

        assert value == "from_root"
        assert elapsed < 0.5, (
            f"1000 DOWN propagations took {elapsed:.2f}s (expected < 0.5s)"
        )

    def test_merge_down_propagation(self, deep_tree):
        """MERGE_DOWN through hierarchy should be fast."""
        current = deep_tree.root
        for i in range(50):
            current = current.get_child(f"level_{i}")

        start = time.perf_counter()
        for _ in range(100):
            value = get_value(current, "config", PropagationMode.MERGE_DOWN)
        elapsed = time.perf_counter() - start

        assert value == {"a": 1, "b": 2, "c": 3}
        assert elapsed < 0.5, (
            f"100 MERGE_DOWN propagations took {elapsed:.2f}s (expected < 0.5s)"
        )

    def test_up_propagation_wide(self):
        """UP propagation aggregating 1000 values should be fast."""
        tree = ResourceTree(root_name="root")
        for i in range(1000):
            tree.create(f"/root/child_{i}", attributes={"value": i})

        start = time.perf_counter()
        for _ in range(10):
            values = get_value(tree.root, "value", PropagationMode.UP)
        elapsed = time.perf_counter() - start

        assert len(values) == 1000
        assert elapsed < 1.0, (
            f"10 UP propagations over 1000 nodes took {elapsed:.2f}s (expected < 1s)"
        )


class TestWildcardPerformance:
    """Performance tests for wildcard query operations."""

    @pytest.fixture
    def query_tree(self):
        """Create a tree for wildcard query tests."""
        tree = ResourceTree(root_name="root")
        for i in range(10):
            tree.create(f"/root/region_{i}")
            for j in range(10):
                tree.create(f"/root/region_{i}/service_{j}")
                for k in range(10):
                    tree.create(
                        f"/root/region_{i}/service_{j}/instance_{k}",
                        attributes={"id": f"{i}-{j}-{k}"},
                    )
        return tree

    def test_single_wildcard_query(self, query_tree):
        """Single wildcard queries should be fast."""
        start = time.perf_counter()
        for _ in range(100):
            results = query_tree.query("/root/*/service_5")
        elapsed = time.perf_counter() - start

        assert len(results) == 10
        assert elapsed < 0.5, (
            f"100 single-wildcard queries took {elapsed:.2f}s (expected < 0.5s)"
        )

    def test_double_wildcard_query(self, query_tree):
        """Double wildcard queries should complete in reasonable time."""
        start = time.perf_counter()
        for _ in range(10):
            results = query_tree.query("/root/**/instance_5")
        elapsed = time.perf_counter() - start

        assert len(results) == 100  # 10 regions * 10 services * 1 instance_5 each
        assert elapsed < 1.0, (
            f"10 double-wildcard queries took {elapsed:.2f}s (expected < 1s)"
        )


class TestSerializationPerformance:
    """Performance tests for serialization operations."""

    @pytest.fixture
    def serialization_tree(self):
        """Create a tree for serialization tests."""
        tree = ResourceTree(root_name="root")
        for i in range(10):
            tree.create(
                f"/root/a_{i}",
                attributes={"data": {"key": f"value_{i}", "nested": {"x": i}}},
            )
            for j in range(10):
                tree.create(f"/root/a_{i}/b_{j}", attributes={"index": j})
        return tree

    def test_to_dict_performance(self, serialization_tree):
        """Converting tree to dict should be fast."""
        start = time.perf_counter()
        for _ in range(100):
            data = serialization_tree.to_dict()
        elapsed = time.perf_counter() - start

        assert "name" in data
        assert elapsed < 0.5, f"100 to_dict calls took {elapsed:.2f}s (expected < 0.5s)"

    def test_from_dict_performance(self, serialization_tree):
        """Creating tree from dict should be fast."""
        data = serialization_tree.to_dict()

        start = time.perf_counter()
        for _ in range(100):
            tree = ResourceTree.from_dict(data)
        elapsed = time.perf_counter() - start

        assert len(tree) == 111  # 1 + 10 + 100
        assert elapsed < 0.5, (
            f"100 from_dict calls took {elapsed:.2f}s (expected < 0.5s)"
        )


class TestProvenancePerformance:
    """Performance tests for provenance tracking."""

    @pytest.fixture
    def provenance_tree(self):
        """Create a tree for provenance tests."""
        tree = ResourceTree(root_name="root")
        tree.root.set_attribute("global", "root_value")

        for i in range(10):
            tree.create(f"/root/level1_{i}", attributes={"level1": f"value_{i}"})
            for j in range(10):
                tree.create(
                    f"/root/level1_{i}/level2_{j}", attributes={"level2": f"value_{j}"}
                )

        return tree

    def test_provenance_tracking_overhead(self, provenance_tree):
        """Provenance tracking should add minimal overhead."""
        leaf = provenance_tree.get("/root/level1_5/level2_5")

        # Without provenance
        start = time.perf_counter()
        for _ in range(1000):
            value = get_value(leaf, "global", PropagationMode.DOWN)
        elapsed_without = time.perf_counter() - start

        # With provenance
        start = time.perf_counter()
        for _ in range(1000):
            prov = get_value(leaf, "global", PropagationMode.DOWN, with_provenance=True)
        elapsed_with = time.perf_counter() - start

        assert value == "root_value"
        assert prov.value == "root_value"
        assert prov.source_path == "/root"

        # Provenance should add less than 2x overhead
        overhead_ratio = elapsed_with / elapsed_without
        assert overhead_ratio < 2.0, (
            f"Provenance overhead {overhead_ratio:.2f}x (expected < 2x)"
        )
