# Provenance

Provenance is HRCP's killer feature: always know exactly where a configuration value came from.

## Why Provenance Matters

In hierarchical systems, a value might come from anywhere in the ancestry chain:

```
/platform           timeout: 30
  /us-east          
    /api            timeout: 60  ← Where does this come from?
    /db                          ← What about this one?
```

Without provenance, debugging configuration issues means manually tracing through the hierarchy. With provenance, the answer is instant.

## Basic Usage

```python
from hrcp import (
    ResourceTree,
    PropagationMode,
    get_value_with_provenance,
)

tree = ResourceTree(root_name="platform")
tree.root.set_attribute("timeout", 30)
tree.create("/platform/us-east/api", attributes={"timeout": 60})
tree.create("/platform/us-east/db")

# Get value with provenance
db = tree.get("/platform/us-east/db")
prov = get_value_with_provenance(db, "timeout", PropagationMode.DOWN)

print(prov.value)        # 30
print(prov.source_path)  # "/platform"
print(prov.mode)         # PropagationMode.DOWN
```

## The Provenance Object

`get_value_with_provenance` returns a `Provenance` object with these attributes:

| Attribute | Description |
|-----------|-------------|
| `value` | The resolved value |
| `source_path` | Path of the resource that provided the value |
| `mode` | The propagation mode used to resolve |

## Provenance with Different Modes

### DOWN Propagation

Shows which ancestor provided the value:

```python
tree = ResourceTree(root_name="org")
tree.root.set_attribute("env", "prod")
tree.create("/org/team", attributes={"env": "staging"})
tree.create("/org/team/project")

project = tree.get("/org/team/project")
prov = get_value_with_provenance(project, "env", PropagationMode.DOWN)

print(prov.value)        # "staging"
print(prov.source_path)  # "/org/team" - closest ancestor with value
```

### NONE Propagation

Shows if the value is set locally:

```python
prov = get_value_with_provenance(project, "env", PropagationMode.NONE)

print(prov.value)        # None
print(prov.source_path)  # None - not set locally
```

### UP Propagation

For UP propagation, provenance tracks all contributing resources:

```python
tree = ResourceTree(root_name="company")
tree.create("/company/eng", attributes={"budget": 100000})
tree.create("/company/sales", attributes={"budget": 50000})

prov = get_value_with_provenance(tree.root, "budget", PropagationMode.UP)
print(prov.value)  # [100000, 50000]
# source_path shows the aggregation point
```

### MERGE_DOWN Propagation

For merged dictionaries, provenance tracks which resource contributed each key:

```python
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("config", {
    "timeout": 30,
    "retries": 3
})
tree.create("/platform/prod", attributes={
    "config": {
        "timeout": 60
    }
})

prod = tree.get("/platform/prod")
prov = get_value_with_provenance(prod, "config", PropagationMode.MERGE_DOWN)

print(prov.value)
# {"timeout": 60, "retries": 3}
# timeout from /platform/prod, retries from /platform
```

## Practical Examples

### Debugging Configuration

When a service has unexpected configuration:

```python
def debug_config(resource, attr):
    """Print where a config value comes from."""
    for mode in [PropagationMode.NONE, PropagationMode.DOWN]:
        prov = get_value_with_provenance(resource, attr, mode)
        if prov.value is not None:
            print(f"{attr} = {prov.value}")
            print(f"  Source: {prov.source_path}")
            print(f"  Mode: {prov.mode.name}")
            return
    print(f"{attr} is not set")

debug_config(api_resource, "timeout")
# timeout = 60
#   Source: /platform/us-east/api
#   Mode: DOWN
```

### Auditing Configuration Sources

Generate a report of where all configuration comes from:

```python
def audit_resource(resource, attributes):
    """Audit configuration sources for a resource."""
    print(f"\nConfiguration audit for {resource.path}")
    print("-" * 50)
    
    for attr in attributes:
        prov = get_value_with_provenance(resource, attr, PropagationMode.DOWN)
        if prov.value is not None:
            local = "(local)" if prov.source_path == resource.path else "(inherited)"
            print(f"  {attr}: {prov.value} {local}")
            if prov.source_path != resource.path:
                print(f"    └─ from {prov.source_path}")
        else:
            print(f"  {attr}: <not set>")

audit_resource(api, ["timeout", "env", "replicas", "region"])
# Configuration audit for /platform/us-east/api
# --------------------------------------------------
#   timeout: 60 (local)
#   env: prod (inherited)
#     └─ from /platform
#   replicas: <not set>
#   region: us-east-1 (inherited)
#     └─ from /platform/us-east
```

### Configuration Diff

Compare effective configuration between resources:

```python
def config_diff(resource1, resource2, attributes):
    """Compare configuration between two resources."""
    print(f"Comparing {resource1.path} vs {resource2.path}\n")
    
    for attr in attributes:
        p1 = get_value_with_provenance(resource1, attr, PropagationMode.DOWN)
        p2 = get_value_with_provenance(resource2, attr, PropagationMode.DOWN)
        
        if p1.value != p2.value:
            print(f"  {attr}:")
            print(f"    {resource1.path}: {p1.value} (from {p1.source_path})")
            print(f"    {resource2.path}: {p2.value} (from {p2.source_path})")
```

## Best Practices

1. **Log provenance in production** - When applying configuration, log where it came from
2. **Use provenance for debugging** - Don't guess, query the source
3. **Build audit tools** - Create utilities that report configuration sources
4. **Test provenance** - Verify values come from expected sources in tests
