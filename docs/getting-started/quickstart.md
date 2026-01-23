# Quick Start

This guide will get you up and running with HRCP in 5 minutes.

## Create a Resource Tree

Everything starts with a `ResourceTree`:

```python
from hrcp import ResourceTree

# Create a tree with a root named "platform"
tree = ResourceTree(root_name="platform")
```

## Add Resources

Create child resources using paths:

```python
# Create nested resources
tree.create("/platform/us-east")
tree.create("/platform/us-east/api")
tree.create("/platform/us-east/db")
tree.create("/platform/eu-west")
tree.create("/platform/eu-west/api")
```

Or create with attributes in one call:

```python
tree.create("/platform/asia/api", attributes={
    "timeout": 45,
    "replicas": 3
})
```

## Set Attributes

Set attributes on any resource:

```python
# Set on root - will be inherited by all children
tree.root.set_attribute("timeout", 30)
tree.root.set_attribute("env", "prod")

# Override on specific resource
api = tree.get("/platform/us-east/api")
api.set_attribute("timeout", 60)  # US East API needs more time
```

## Get Values

Use propagation modes to resolve values:

```python
from hrcp import get_value, PropagationMode

# Get a resource
db = tree.get("/platform/us-east/db")

# Get inherited value (flows DOWN from ancestors)
timeout = get_value(db, "timeout", PropagationMode.DOWN)
print(timeout)  # 30 - inherited from root
```

## Track Provenance

Know exactly where values come from:

```python
prov = get_value(db, "timeout", PropagationMode.DOWN, with_provenance=True)
print(f"Value: {prov.value}")           # 30
print(f"Source: {prov.source_path}")    # /platform
print(f"Mode: {prov.mode}")             # PropagationMode.DOWN
```

## Complete Example

```python
from hrcp import ResourceTree, PropagationMode, get_value

# Build hierarchy
tree = ResourceTree(root_name="org")
tree.root.set_attribute("budget_code", "CORP-001")
tree.root.set_attribute("tier", "standard")

tree.create("/org/engineering", attributes={"tier": "premium"})
tree.create("/org/engineering/platform")
tree.create("/org/engineering/platform/api", attributes={"port": 8080})
tree.create("/org/marketing")

# Query values
api = tree.get("/org/engineering/platform/api")

# Local value
port = get_value(api, "port", PropagationMode.NONE)
print(f"Port: {port}")  # 8080

# Inherited values
tier = get_value(api, "tier", PropagationMode.DOWN)
print(f"Tier: {tier}")  # premium (from /org/engineering)

budget = get_value(api, "budget_code", PropagationMode.DOWN)
print(f"Budget: {budget}")  # CORP-001 (from root)

# Provenance
prov = get_value(api, "tier", PropagationMode.DOWN, with_provenance=True)
print(f"Tier '{prov.value}' comes from {prov.source_path}")
# Tier 'premium' comes from /org/engineering
```

## Next Steps

- Learn about [Propagation Modes](../guide/propagation.md) in detail
- Understand [Provenance](../guide/provenance.md) tracking
- Explore [Wildcards](../guide/wildcards.md) for querying multiple resources
- Add [Schema Validation](../guide/schema.md) to your attributes
