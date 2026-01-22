# HRCP

**Hierarchical Resource Configuration with Provenance**

<div class="grid cards" markdown>

-   :material-tree:{ .lg .middle } __Hierarchical__

    ---

    Build tree structures that mirror your organization, infrastructure, or domain model.

-   :material-arrow-down-bold:{ .lg .middle } __Inheritance__

    ---

    Set defaults at the top, override at any level. Values cascade naturally.

-   :material-arrow-up-bold:{ .lg .middle } __Aggregation__

    ---

    Roll up values from children. Collect metrics, sum headcounts, gather configs.

-   :material-fingerprint:{ .lg .middle } __Provenance__

    ---

    Always know where a value came from. Debug config issues in seconds.

</div>

## The Problem

Configuration in hierarchical systems (orgs → teams → projects, regions → clusters → services) needs:

- **Inheritance**: Set defaults at the top, override below
- **Aggregation**: Roll up values from children  
- **Traceability**: Know exactly which node provided each value

HRCP solves this with ~2000 lines of dependency-free Python.

## Quick Example

```python
from hrcp import ResourceTree, PropagationMode, get_effective_value

# Build a hierarchy
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("timeout", 30)
tree.root.set_attribute("env", "prod")

tree.create("/platform/us-east/api", attributes={"timeout": 60})
tree.create("/platform/us-east/db")

# Inheritance: values flow DOWN
api = tree.get("/platform/us-east/api")
timeout = get_effective_value(api, "timeout", PropagationMode.DOWN)
# timeout == 60 (local override)

db = tree.get("/platform/us-east/db")
timeout = get_effective_value(db, "timeout", PropagationMode.DOWN)
# timeout == 30 (inherited from root)
```

## Why HRCP?

| Feature | HRCP | Flat Config | Environment Variables |
|---------|------|-------------|----------------------|
| Hierarchical inheritance | ✅ | ❌ | ❌ |
| Value aggregation | ✅ | ❌ | ❌ |
| Provenance tracking | ✅ | ❌ | ❌ |
| Type validation | ✅ | Varies | ❌ |
| Zero dependencies | ✅ | Varies | ✅ |

## Installation

```bash
pip install hrcp
```

Ready to dive in? Check out the [Quick Start](getting-started/quickstart.md) guide.
