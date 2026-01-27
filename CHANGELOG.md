# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Python 3.14 support
- New propagation modes:
  - `REQUIRE_PATH`: Returns value only if ALL ancestors have truthy values (opt-in features)
  - `COLLECT_ANCESTORS`: Collects all ancestor values as a list (custom AND/OR logic)

### Changed
- Renamed propagation modes for clarity (backward-compatible aliases provided):
  - `DOWN` → `INHERIT` (values inherit from ancestors)
  - `UP` → `AGGREGATE` (values collected from descendants)
  - `MERGE_DOWN` → `MERGE` (deep merge from ancestors)

### Deprecated
- `PropagationMode.DOWN` (use `INHERIT`)
- `PropagationMode.UP` (use `AGGREGATE`)
- `PropagationMode.MERGE_DOWN` (use `MERGE`)
- Dict schema reference in serialization documentation
- Clarified UP mode provenance with `source_path` vs `contributing_paths` explanation
- Troubleshooting guide with common errors and debugging tips
- Split examples into individual pages for better navigation:
  - Multi-Tenant SaaS, Infrastructure Config, Feature Flags
  - Budget Rollup, Access Control, Kubernetes Namespaces
  - GitOps Config, Multi-Cloud, Game Servers
  - E-commerce Catalog, Configuration Audit
- Examples overview page with domain groupings and pattern summaries
- Thread safety documentation with concurrency patterns
- Corrected installation docs (HRCP is truly zero-dependency)
- Added examples for using YAML/TOML via `to_dict()`
- CI status badge in README
- `Resource` class added to API reference documentation
- Performance test suite covering tree creation, lookup, propagation, wildcards, serialization, and provenance
- Benchmark script (`bench/benchmark.py`) for detailed performance analysis with ops/sec metrics
- Documentation example tests (`tests/test_doc_examples.py`) ensuring all doc examples work correctly

### Fixed
- Fixed provenance documentation for NONE mode (returns `None`, not `Provenance` with null values)
- Corrected line count from "~1200/~2000" to "~1000" in README and docs
- Fixed `query_values()` documentation (returns list, not dict)
- CI workflow for tests, linting, and type checking on all PRs
- Dynamic Python version extraction in CI (follows attrs pattern via `hynek/build-and-inspect-python-package`)
- Tox configuration for multi-Python version testing (3.11, 3.12, 3.13, 3.14)
- `tox-uv` integration for faster virtual environment creation
- Malformed data handling tests for serialization
- Export `Resource` class from top-level `hrcp` module
- `key_sources` and `contributing_paths` documented in provenance guide

### Fixed
- Type validation in `tree_from_dict` now raises `TypeError` for wrong types
- Mypy error in `query_values` with `isinstance` check

## [0.2.0] - 2025-01-23

### Added
- Wildcard support (`*` and `**`) for querying multiple resources
- `query()` method for pattern-based resource lookup
- `query_values()` method for getting values across multiple resources
- Provenance tracking with `key_sources` for MERGE_DOWN mode
- Provenance tracking with `contributing_paths` for UP mode

### Changed
- Improved documentation with more examples

## [0.1.0] - 2025-01-22

### Added
- Initial release
- `ResourceTree` for hierarchical configuration management
- `Resource` class for individual nodes
- Four propagation modes: `NONE`, `DOWN`, `UP`, `MERGE_DOWN`
- `Provenance` tracking for all values
- JSON serialization (`to_json`, `from_json`)
- Dict serialization (`to_dict`, `from_dict`)
- Full test suite with Hypothesis property-based testing

[Unreleased]: https://github.com/keongalvin/hrcp/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/keongalvin/hrcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/keongalvin/hrcp/releases/tag/v0.1.0
