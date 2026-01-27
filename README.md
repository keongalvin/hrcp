# HRCP

**Hierarchical Resource Configuration with Provenance**

[![CI](https://github.com/keongalvin/hrcp/actions/workflows/ci.yaml/badge.svg)](https://github.com/keongalvin/hrcp/actions/workflows/ci.yaml)
[![PyPI version](https://img.shields.io/pypi/v/hrcp.svg)](https://pypi.org/project/hrcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/hrcp.svg)](https://pypi.org/project/hrcp/)
[![License](https://img.shields.io/pypi/l/hrcp.svg)](https://github.com/keongalvin/hrcp/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue.svg)](https://hrcp.readthedocs.io/)

A minimal Python library for hierarchical configuration where you always know where values came from.

## The Problem

Configuration in hierarchical systems (orgs → teams → projects, regions → clusters → services) needs:
- **Inheritance**: Set defaults at the top, override below
- **Aggregation**: Roll up values from children
- **Traceability**: Know exactly which node provided each value

HRCP solves this with ~1000 lines of dependency-free Python.

## Installation

```bash
pip install hrcp
```

## Quick Example

```python
from hrcp import ResourceTree, PropagationMode, get_value

# Build a hierarchy
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("timeout", 30)
tree.root.set_attribute("env", "prod")

tree.create("/platform/us-east/api", attributes={"timeout": 60})
tree.create("/platform/us-east/db")
tree.create("/platform/eu-west/api")

# Inheritance: values flow from ancestors
api = tree.get("/platform/us-east/api")
timeout = get_value(api, "timeout", PropagationMode.INHERIT)
# timeout == 60 (local override)

db = tree.get("/platform/us-east/db")
timeout = get_value(db, "timeout", PropagationMode.INHERIT)
# timeout == 30 (inherited from root)

# Provenance: know where it came from
prov = get_value(db, "timeout", PropagationMode.INHERIT, with_provenance=True)
print(prov.value)        # 30
print(prov.source_path)  # "/platform" - the root provided this value
```

## Propagation Modes

| Mode | Direction | Use Case |
|------|-----------|----------|
| `INHERIT` | Ancestors → Resource | Inherit defaults, allow overrides |
| `AGGREGATE` | Descendants → Resource | Aggregate values, collect metrics |
| `MERGE` | Ancestors → Resource | Deep-merge dictionaries |
| `REQUIRE_PATH` | Ancestors → Resource | All ancestors must have truthy values |
| `COLLECT_ANCESTORS` | Ancestors → Resource | Collect all ancestor values as list |
| `NONE` | Local only | Get only directly set values |

### INHERIT - Inherit from Ancestors

Values cascade from parent to children. Closest ancestor wins.

```python
tree.root.set_attribute("tier", "premium")
tree.create("/org/team/project")

project = tree.get("/org/team/project")
tier = get_value(project, "tier", PropagationMode.INHERIT)
# "premium" - inherited from root
```

### AGGREGATE - Aggregate from Descendants

Collect all values from the subtree.

```python
tree.create("/org/team1", attributes={"headcount": 5})
tree.create("/org/team2", attributes={"headcount": 8})

counts = get_value(tree.root, "headcount", PropagationMode.AGGREGATE)
# [5, 8]
```

### MERGE - Deep Dict Merge

Recursively merge dicts through the hierarchy.

```python
tree.root.set_attribute("config", {"db": {"host": "localhost", "port": 5432}})
tree.create("/org/prod", attributes={"config": {"db": {"host": "prod.db.internal"}}})

prod = tree.get("/org/prod")
config = get_value(prod, "config", PropagationMode.MERGE)
# {"db": {"host": "prod.db.internal", "port": 5432}}
```

### REQUIRE_PATH - All Ancestors Must Enable

Returns value only if ALL ancestors have truthy values. Perfect for opt-in features.

```python
tree.root.set_attribute("feature_enabled", True)
tree.create("/org", attributes={"feature_enabled": True})
account = tree.create("/org/account", attributes={"feature_enabled": True})

# All ancestors enabled → returns True
enabled = get_value(account, "feature_enabled", PropagationMode.REQUIRE_PATH)
# True

# If ANY ancestor is False or missing → returns None
```

## Provenance

The killer feature. Always know where a value came from:

```python
prov = get_value(resource, "timeout", PropagationMode.INHERIT, with_provenance=True)
prov.value        # The resolved value
prov.source_path  # Path of the resource that provided it
prov.mode         # The propagation mode used
```

For MERGE, provenance tracks which resource contributed each key via `prov.key_sources`.

## Wildcards

Query multiple resources at once:

```python
# * matches one segment
tree.query("/platform/*/api")

# ** matches any depth
tree.query("/platform/**/config")

# Get values across matches
tree.query_values("/platform/*/api", "port", PropagationMode.NONE)
```

## Serialization

```python
# JSON
tree.to_json("config.json")
tree = ResourceTree.from_json("config.json")

# Dict
data = tree.to_dict()
tree = ResourceTree.from_dict(data)
```

## Use Cases

**Multi-tenant SaaS**
```
/platform
  timeout: 30
  /tenant-a        # inherits timeout=30
    /project-1
  /tenant-b
    timeout: 60    # override for this tenant
    /project-2     # inherits timeout=60
```

**Infrastructure Config**
```
/infra
  region: us-east-1
  /prod
    /api
      replicas: 3
    /worker
      replicas: 5
  /staging          # inherits region
    /api
      replicas: 1
```

**Feature Flags**
```
/features
  dark_mode: false
  /beta_users
    dark_mode: true   # beta users get dark mode
    /user-123         # inherits dark_mode=true
```

## Documentation

Full documentation at [hrcp.readthedocs.io](https://hrcp.readthedocs.io/), including:

- [Quick Start Guide](https://hrcp.readthedocs.io/en/latest/getting-started/quickstart/)
- [Propagation Modes](https://hrcp.readthedocs.io/en/latest/guide/propagation/)
- [Provenance Tracking](https://hrcp.readthedocs.io/en/latest/guide/provenance/)
- [API Reference](https://hrcp.readthedocs.io/en/latest/api/hrcp/)

## Requirements

- Python 3.11+
- Zero dependencies

## Development

```bash
# Clone the repository
git clone https://github.com/keongalvin/hrcp.git
cd hrcp

# Install with dev dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run benchmarks
uv run python bench/benchmark.py

# Build docs locally
uv run mkdocs serve
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key points:
- We follow strict **Test-Driven Development** (TDD)
- Write failing tests first, then implement
- No mocks or monkeypatching - use pure data models
- Run `uv run pytest` and `uv run ruff check .` before submitting

## License

MIT
