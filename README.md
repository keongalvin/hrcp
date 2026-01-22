# HRCP

**Hierarchical Resource Configuration with Provenance**

A minimal Python library for hierarchical configuration where you always know where values came from.

## The Problem

Configuration in hierarchical systems (orgs → teams → projects, regions → clusters → services) needs:
- **Inheritance**: Set defaults at the top, override below
- **Aggregation**: Roll up values from children
- **Traceability**: Know exactly which node provided each value

HRCP solves this with ~2000 lines of dependency-free Python.

## Installation

```bash
pip install hrcp
```

## Quick Example

```python
from hrcp import ResourceTree, PropagationMode, get_effective_value, get_value_with_provenance

# Build a hierarchy
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("timeout", 30)
tree.root.set_attribute("env", "prod")

tree.create("/platform/us-east/api", attributes={"timeout": 60})
tree.create("/platform/us-east/db")
tree.create("/platform/eu-west/api")

# Inheritance: values flow DOWN
api = tree.get("/platform/us-east/api")
timeout = get_effective_value(api, "timeout", PropagationMode.DOWN)
# timeout == 60 (local override)

db = tree.get("/platform/us-east/db")
timeout = get_effective_value(db, "timeout", PropagationMode.DOWN)
# timeout == 30 (inherited from root)

# Provenance: know where it came from
prov = get_value_with_provenance(db, "timeout", PropagationMode.DOWN)
print(prov.value)        # 30
print(prov.source_path)  # "/platform" - the root provided this value
```

## Propagation Modes

### DOWN - Inherit from Ancestors

Values cascade from parent to children. Closest ancestor wins.

```python
tree.root.set_attribute("tier", "premium")
tree.create("/org/team/project")

project = tree.get("/org/team/project")
tier = get_effective_value(project, "tier", PropagationMode.DOWN)
# "premium" - inherited from root
```

### UP - Aggregate from Descendants

Collect all values from the subtree.

```python
tree.create("/org/team1", attributes={"headcount": 5})
tree.create("/org/team2", attributes={"headcount": 8})

counts = get_effective_value(tree.root, "headcount", PropagationMode.UP)
# [5, 8]
```

### MERGE_DOWN - Deep Dict Merge

Recursively merge dicts through the hierarchy.

```python
tree.root.set_attribute("config", {"db": {"host": "localhost", "port": 5432}})
tree.create("/org/prod", attributes={"config": {"db": {"host": "prod.db.internal"}}})

prod = tree.get("/org/prod")
config = get_effective_value(prod, "config", PropagationMode.MERGE_DOWN)
# {"db": {"host": "prod.db.internal", "port": 5432}}
```

### NONE - Local Only

Only return the value if set directly on the resource.

## Provenance

The killer feature. Always know where a value came from:

```python
from hrcp import get_value_with_provenance

prov = get_value_with_provenance(resource, "timeout", PropagationMode.DOWN)
prov.value        # The resolved value
prov.source_path  # Path of the resource that provided it
prov.mode         # The propagation mode used
```

For MERGE_DOWN, provenance tracks which resource contributed each key.

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

## Schema Validation

Enforce constraints:

```python
tree.define("port", type_=int, ge=1, le=65535)
tree.define("env", choices=("dev", "staging", "prod"))

tree.root.set_attribute("port", 8080)      # OK
tree.root.set_attribute("port", "bad")     # ValidationError
tree.root.set_attribute("port", 99999)     # ValidationError
```

## Serialization

```python
# JSON
tree.to_json("config.json")
tree = ResourceTree.from_json("config.json")

# YAML
tree.to_yaml("config.yaml")
tree = ResourceTree.from_yaml_file("config.yaml")

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

## License

MIT
