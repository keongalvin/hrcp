# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI workflow for tests, linting, and type checking on all PRs
- Tox configuration for multi-Python version testing (3.11, 3.12, 3.13)
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
