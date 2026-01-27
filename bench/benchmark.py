"""Performance benchmarks for HRCP.

Run with: python bench/benchmark.py
Or with uv: uv run bench/benchmark.py

Results are printed in a formatted table showing operations per second
and time per operation for each benchmark.
"""

from __future__ import annotations

import gc
import statistics
import time
from dataclasses import dataclass
from typing import Callable

from hrcp import PropagationMode
from hrcp import ResourceTree
from hrcp import get_value


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""

    name: str
    iterations: int
    total_time: float
    times: list[float]

    @property
    def ops_per_sec(self) -> float:
        """Operations per second."""
        return self.iterations / self.total_time

    @property
    def time_per_op_us(self) -> float:
        """Microseconds per operation."""
        return (self.total_time / self.iterations) * 1_000_000

    @property
    def std_dev_us(self) -> float:
        """Standard deviation in microseconds."""
        if len(self.times) < 2:
            return 0.0
        return statistics.stdev(self.times) * 1_000_000


def benchmark(
    name: str,
    func: Callable[[], None],
    iterations: int = 1000,
    warmup: int = 100,
    runs: int = 5,
) -> BenchmarkResult:
    """Run a benchmark and return results.

    Args:
        name: Name of the benchmark.
        func: Function to benchmark (called with no arguments).
        iterations: Number of iterations per run.
        warmup: Number of warmup iterations before timing.
        runs: Number of timed runs for statistics.

    Returns:
        BenchmarkResult with timing data.
    """
    # Warmup (also helps populate any internal caches)
    for _ in range(warmup):
        func()

    # Collect garbage before timing to reduce noise
    gc.collect()
    gc.disable()  # Disable GC during benchmarking for consistency

    try:
        # Timed runs
        times = []
        for _ in range(runs):
            # Force fresh state by collecting garbage between runs
            gc.enable()
            gc.collect()
            gc.disable()

            start = time.perf_counter()
            for _ in range(iterations):
                func()
            elapsed = time.perf_counter() - start
            times.append(elapsed / iterations)

        total_time = sum(times) * iterations

        return BenchmarkResult(
            name=name,
            iterations=iterations * runs,
            total_time=total_time,
            times=times,
        )
    finally:
        gc.enable()  # Re-enable GC


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results in a formatted table."""
    print()
    print("=" * 80)
    print("HRCP Performance Benchmarks")
    print("=" * 80)
    print()
    print(f"{'Benchmark':<45} {'ops/sec':>12} {'μs/op':>10} {'std dev':>10}")
    print("-" * 80)

    current_category = ""
    for result in results:
        # Extract category from name (before the colon)
        category = result.name.split(":")[0] if ":" in result.name else ""
        if category != current_category:
            if current_category:
                print()
            current_category = category

        print(
            f"{result.name:<45} "
            f"{result.ops_per_sec:>12,.0f} "
            f"{result.time_per_op_us:>10.2f} "
            f"{result.std_dev_us:>10.2f}"
        )

    print("-" * 80)
    print()


# =============================================================================
# Benchmark Fixtures
# =============================================================================


def create_wide_tree(n: int = 1000) -> ResourceTree:
    """Create a tree with n children at root level."""
    tree = ResourceTree(root_name="root")
    for i in range(n):
        tree.create(f"/root/child_{i}", attributes={"index": i})
    return tree


def create_deep_tree(depth: int = 50) -> ResourceTree:
    """Create a tree with specified depth."""
    tree = ResourceTree(root_name="root")
    tree.root.set_attribute("inherited", "from_root")
    tree.root.set_attribute("config", {"a": 1, "b": 2, "c": 3})

    path = "/root"
    for i in range(depth):
        path = f"{path}/level_{i}"
        tree.create(path, attributes={"depth": i})

    return tree


def create_balanced_tree() -> ResourceTree:
    """Create a balanced tree: 10 x 10 x 10 = 1000 leaves."""
    tree = ResourceTree(root_name="root")
    tree.root.set_attribute("global", "value")

    for i in range(10):
        tree.create(f"/root/a_{i}", attributes={"level": 1})
        for j in range(10):
            tree.create(f"/root/a_{i}/b_{j}", attributes={"level": 2})
            for k in range(10):
                tree.create(
                    f"/root/a_{i}/b_{j}/c_{k}",
                    attributes={"level": 3, "id": f"{i}-{j}-{k}"},
                )

    return tree


# =============================================================================
# Benchmarks
# =============================================================================


def run_creation_benchmarks() -> list[BenchmarkResult]:
    """Run tree creation benchmarks."""
    results = []

    # Create single resource
    def create_single():
        tree = ResourceTree(root_name="root")
        tree.create("/root/child", attributes={"key": "value"})

    results.append(
        benchmark("creation: single resource", create_single, iterations=5000)
    )

    # Create tree with 100 children
    def create_100_children():
        tree = ResourceTree(root_name="root")
        for i in range(100):
            tree.create(f"/root/child_{i}")

    results.append(
        benchmark("creation: 100 children", create_100_children, iterations=100)
    )

    # Create deep path (10 levels)
    def create_deep_path():
        tree = ResourceTree(root_name="root")
        tree.create("/root/a/b/c/d/e/f/g/h/i/j")

    results.append(
        benchmark("creation: depth-10 path", create_deep_path, iterations=1000)
    )

    return results


def run_lookup_benchmarks() -> list[BenchmarkResult]:
    """Run resource lookup benchmarks."""
    results = []

    # Setup trees
    wide_tree = create_wide_tree(1000)
    deep_tree = create_deep_tree(50)
    balanced_tree = create_balanced_tree()

    # Get by path (wide tree)
    def get_wide():
        wide_tree.get("/root/child_500")

    results.append(
        benchmark("lookup: get from 1000 siblings", get_wide, iterations=10000)
    )

    # Get by path (deep tree)
    deep_path = "/root" + "".join(f"/level_{i}" for i in range(50))

    def get_deep():
        deep_tree.get(deep_path)

    results.append(benchmark("lookup: get at depth 50", get_deep, iterations=10000))

    # Get by path (balanced tree)
    def get_balanced():
        balanced_tree.get("/root/a_5/b_5/c_5")

    results.append(
        benchmark("lookup: get from balanced tree", get_balanced, iterations=10000)
    )

    # Walk entire tree
    def walk_tree():
        list(balanced_tree.walk())

    results.append(benchmark("lookup: walk 1111 nodes", walk_tree, iterations=500))

    return results


def run_propagation_benchmarks() -> list[BenchmarkResult]:
    """Run value propagation benchmarks."""
    results = []

    # Setup
    deep_tree = create_deep_tree(50)
    deep_path = "/root" + "".join(f"/level_{i}" for i in range(50))
    deep_leaf = deep_tree.get(deep_path)

    wide_tree = create_wide_tree(1000)

    balanced_tree = create_balanced_tree()
    balanced_leaf = balanced_tree.get("/root/a_5/b_5/c_5")

    # DOWN propagation (deep)
    def down_deep():
        get_value(deep_leaf, "inherited", PropagationMode.DOWN)

    results.append(benchmark("propagation: DOWN depth-50", down_deep, iterations=5000))

    # DOWN propagation (balanced)
    def down_balanced():
        get_value(balanced_leaf, "global", PropagationMode.DOWN)

    results.append(
        benchmark("propagation: DOWN balanced tree", down_balanced, iterations=5000)
    )

    # MERGE_DOWN propagation
    def merge_down():
        get_value(deep_leaf, "config", PropagationMode.MERGE_DOWN)

    results.append(
        benchmark("propagation: MERGE_DOWN depth-50", merge_down, iterations=1000)
    )

    # UP propagation (wide)
    def up_wide():
        get_value(wide_tree.root, "index", PropagationMode.UP)

    results.append(benchmark("propagation: UP 1000 children", up_wide, iterations=100))

    # UP propagation (balanced)
    def up_balanced():
        get_value(balanced_tree.root, "id", PropagationMode.UP)

    results.append(
        benchmark("propagation: UP 1000 leaves", up_balanced, iterations=100)
    )

    # NONE propagation
    def none_local():
        get_value(deep_leaf, "depth", PropagationMode.NONE)

    results.append(benchmark("propagation: NONE local", none_local, iterations=10000))

    return results


def run_provenance_benchmarks() -> list[BenchmarkResult]:
    """Run provenance tracking benchmarks."""
    results = []

    # Setup
    deep_tree = create_deep_tree(50)
    deep_path = "/root" + "".join(f"/level_{i}" for i in range(50))
    deep_leaf = deep_tree.get(deep_path)

    wide_tree = create_wide_tree(100)

    # DOWN with provenance
    def down_prov():
        get_value(deep_leaf, "inherited", PropagationMode.DOWN, with_provenance=True)

    results.append(benchmark("provenance: DOWN depth-50", down_prov, iterations=5000))

    # MERGE_DOWN with provenance
    def merge_prov():
        get_value(deep_leaf, "config", PropagationMode.MERGE_DOWN, with_provenance=True)

    results.append(
        benchmark("provenance: MERGE_DOWN depth-50", merge_prov, iterations=1000)
    )

    # UP with provenance
    def up_prov():
        get_value(wide_tree.root, "index", PropagationMode.UP, with_provenance=True)

    results.append(benchmark("provenance: UP 100 children", up_prov, iterations=500))

    return results


def run_wildcard_benchmarks() -> list[BenchmarkResult]:
    """Run wildcard query benchmarks."""
    results = []

    # Setup
    balanced_tree = create_balanced_tree()

    # Single wildcard
    def single_wildcard():
        balanced_tree.query("/root/*/b_5")

    results.append(benchmark("wildcard: /root/*/b_5", single_wildcard, iterations=500))

    # Double wildcard (specific suffix)
    def double_wildcard_suffix():
        balanced_tree.query("/root/**/c_5")

    results.append(
        benchmark("wildcard: /root/**/c_5", double_wildcard_suffix, iterations=100)
    )

    # Double wildcard (all)
    def double_wildcard_all():
        balanced_tree.query("/root/**")

    results.append(
        benchmark("wildcard: /root/** (all 1111)", double_wildcard_all, iterations=100)
    )

    # Query values
    def query_values():
        balanced_tree.query_values("/root/*/b_5", "level", PropagationMode.NONE)

    results.append(benchmark("wildcard: query_values", query_values, iterations=500))

    return results


def run_serialization_benchmarks() -> list[BenchmarkResult]:
    """Run serialization benchmarks."""
    results = []

    # Setup
    balanced_tree = create_balanced_tree()
    tree_dict = balanced_tree.to_dict()

    # to_dict
    def to_dict():
        balanced_tree.to_dict()

    results.append(
        benchmark("serialization: to_dict 1111 nodes", to_dict, iterations=200)
    )

    # from_dict
    def from_dict():
        ResourceTree.from_dict(tree_dict)

    results.append(
        benchmark("serialization: from_dict 1111 nodes", from_dict, iterations=200)
    )

    return results


def run_attribute_benchmarks() -> list[BenchmarkResult]:
    """Run attribute operation benchmarks."""
    results = []

    # Setup
    tree = ResourceTree(root_name="root")
    tree.create("/root/child")
    resource = tree.get("/root/child")

    # Set attribute
    counter = [0]

    def set_attr():
        resource.set_attribute(f"key_{counter[0]}", counter[0])
        counter[0] += 1

    results.append(benchmark("attribute: set", set_attr, iterations=10000))

    # Get attribute (exists)
    resource.set_attribute("existing", "value")

    def get_attr_exists():
        resource.get_attribute("existing")

    results.append(
        benchmark("attribute: get (exists)", get_attr_exists, iterations=10000)
    )

    # Get attribute (missing)
    def get_attr_missing():
        resource.get_attribute("nonexistent")

    results.append(
        benchmark("attribute: get (missing)", get_attr_missing, iterations=10000)
    )

    return results


def main() -> None:
    """Run all benchmarks and print results."""
    print("Running HRCP benchmarks...")
    print("This may take a minute...")

    all_results = []

    all_results.extend(run_creation_benchmarks())
    all_results.extend(run_lookup_benchmarks())
    all_results.extend(run_attribute_benchmarks())
    all_results.extend(run_propagation_benchmarks())
    all_results.extend(run_provenance_benchmarks())
    all_results.extend(run_wildcard_benchmarks())
    all_results.extend(run_serialization_benchmarks())

    print_results(all_results)

    # Summary statistics
    total_ops = sum(r.iterations for r in all_results)
    total_time = sum(r.total_time for r in all_results)
    print(f"Total: {total_ops:,} operations in {total_time:.2f}s")
    print()


if __name__ == "__main__":
    main()
