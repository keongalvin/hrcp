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
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="platform")
tree.root.set_attribute("timeout", 30)
tree.create("/platform/us-east/api", attributes={"timeout": 60})
tree.create("/platform/us-east/db")

# Get value with provenance
db = tree.get("/platform/us-east/db")
prov = get_value(db, "timeout", PropagationMode.INHERIT, with_provenance=True)

print(prov.value)        # 30
print(prov.source_path)  # "/platform"
print(prov.mode)         # PropagationMode.INHERIT
```

## The Provenance Object

`get_value(..., with_provenance=True)` returns a `Provenance` object with these attributes:

| Attribute | Description |
|-----------|-------------|
| `value` | The resolved value |
| `source_path` | Path of the resource that provided the value |
| `mode` | The propagation mode used to resolve |
| `key_sources` | For MERGE with dict values, maps each key to the path that provided it (uses dot notation for nested keys) |
| `contributing_paths` | For UP aggregation, lists all resource paths that contributed values |

## Provenance with Different Modes

### INHERIT Propagation

Shows which ancestor provided the value:

```python
tree = ResourceTree(root_name="org")
tree.root.set_attribute("env", "prod")
tree.create("/org/team", attributes={"env": "staging"})
tree.create("/org/team/project")

project = tree.get("/org/team/project")
prov = get_value(project, "env", PropagationMode.INHERIT, with_provenance=True)

print(prov.value)        # "staging"
print(prov.source_path)  # "/org/team" - closest ancestor with value
```

### NONE Propagation

Shows if the value is set locally:

```python
tree = ResourceTree(root_name="org")
tree.create("/org/team")
project = tree.create("/org/team/project")

# When attribute IS set locally
project.set_attribute("env", "staging")
prov = get_value(project, "env", PropagationMode.NONE, with_provenance=True)

print(prov.value)        # "staging"
print(prov.source_path)  # "/org/team/project"

# When attribute is NOT set locally
prov = get_value(project, "other", PropagationMode.NONE, with_provenance=True)
print(prov)  # None - returns None, not a Provenance object
```

!!! note "Return Value"
    When an attribute is not found, `get_value(..., with_provenance=True)` returns `None`, not a Provenance object with null values. Always check for `None` before accessing `.value`.

### UP Propagation

For UP propagation, provenance tracks all contributing resources. Note the distinction between two fields:

- **`source_path`**: The resource where aggregation was performed (where you called `get_value`)
- **`contributing_paths`**: All resources in the subtree that had the attribute

```python
tree = ResourceTree(root_name="company")
tree.create("/company/eng", attributes={"budget": 100000})
tree.create("/company/sales", attributes={"budget": 50000})

prov = get_value(tree.root, "budget", PropagationMode.AGGREGATE, with_provenance=True)

print(prov.value)  # [100000, 50000]
print(prov.source_path)  # "/company" (the aggregation point - where you queried)
print(prov.contributing_paths)  # ["/company/eng", "/company/sales"] (where values came from)
```

!!! tip "Understanding UP Provenance"
    Think of `source_path` as "where did I ask?" and `contributing_paths` as "where did the values come from?"

### MERGE Propagation

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
prov = get_value(prod, "config", PropagationMode.MERGE, with_provenance=True)

print(prov.value)
# {"timeout": 60, "retries": 3}

print(prov.key_sources)
# {"timeout": "/platform/prod", "retries": "/platform"}
```

## Practical Examples

### Debugging Configuration

When a service has unexpected configuration:

```python
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("timeout", 30)
api_resource = tree.create("/platform/us-east/api", attributes={"timeout": 60})

def debug_config(resource, attr):
    """Print where a config value comes from."""
    for mode in [PropagationMode.NONE, PropagationMode.INHERIT]:
        prov = get_value(resource, attr, mode, with_provenance=True)
        if prov and prov.value is not None:
            print(f"{attr} = {prov.value}")
            print(f"  Source: {prov.source_path}")
            print(f"  Mode: {prov.mode.name}")
            return
    print(f"{attr} is not set")

debug_config(api_resource, "timeout")
# timeout = 60
#   Source: /platform/us-east/api
#   Mode: NONE
```

### Auditing Configuration Sources

Generate a report of where all configuration comes from:

```python
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("env", "prod")
tree.create("/platform/us-east", attributes={"region": "us-east-1"})
api = tree.create("/platform/us-east/api", attributes={"timeout": 60})

def audit_resource(resource, attributes):
    """Audit configuration sources for a resource."""
    print(f"\nConfiguration audit for {resource.path}")
    print("-" * 50)

    for attr in attributes:
        prov = get_value(resource, attr, PropagationMode.INHERIT, with_provenance=True)
        if prov and prov.value is not None:
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
        p1 = get_value(resource1, attr, PropagationMode.INHERIT, with_provenance=True)
        p2 = get_value(resource2, attr, PropagationMode.INHERIT, with_provenance=True)

        v1 = p1.value if p1 else None
        v2 = p2.value if p2 else None

        if v1 != v2:
            print(f"  {attr}:")
            print(f"    {resource1.path}: {v1} (from {p1.source_path if p1 else 'N/A'})")
            print(f"    {resource2.path}: {v2} (from {p2.source_path if p2 else 'N/A'})")
```

## Best Practices

1. **Log provenance in production** - When applying configuration, log where it came from
2. **Use provenance for debugging** - Don't guess, query the source
3. **Build audit tools** - Create utilities that report configuration sources
4. **Test provenance** - Verify values come from expected sources in tests
