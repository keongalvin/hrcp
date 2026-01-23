# Propagation Modes

Propagation modes control how attribute values flow through the resource tree. Choosing the right mode is key to effective hierarchical configuration.

## Overview

| Mode | Direction | Use Case |
|------|-----------|----------|
| `DOWN` | Ancestors → Resource | Inherit defaults, allow overrides |
| `UP` | Descendants → Resource | Aggregate values, collect metrics |
| `MERGE_DOWN` | Ancestors → Resource | Deep-merge dictionaries |
| `NONE` | Local only | Get only directly set values |

## DOWN - Inherit from Ancestors

Values cascade from parent to children. The **closest ancestor** with the attribute wins.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="org")
tree.root.set_attribute("timeout", 30)

tree.create("/org/team", attributes={"timeout": 60})
tree.create("/org/team/project")
tree.create("/org/team/project/service")

# Each resource inherits from closest ancestor with the value
root_timeout = get_value(tree.root, "timeout", PropagationMode.DOWN)
# 30 - set locally

team_timeout = get_value(tree.get("/org/team"), "timeout", PropagationMode.DOWN)
# 60 - set locally (overrides parent)

project_timeout = get_value(tree.get("/org/team/project"), "timeout", PropagationMode.DOWN)
# 60 - inherited from /org/team

service_timeout = get_value(tree.get("/org/team/project/service"), "timeout", PropagationMode.DOWN)
# 60 - inherited from /org/team (closest ancestor)
```

### When to Use DOWN

- **Default configurations** that should apply to all children
- **Environment settings** (production, staging, development)
- **Policy values** that cascade through a hierarchy
- **Feature flags** that can be overridden at any level

## UP - Aggregate from Descendants

Collect all values from the subtree beneath a resource.

```python
tree = ResourceTree(root_name="company")

tree.create("/company/eng", attributes={"headcount": 50})
tree.create("/company/eng/platform", attributes={"headcount": 15})
tree.create("/company/eng/mobile", attributes={"headcount": 10})
tree.create("/company/sales", attributes={"headcount": 30})

# Aggregate from all descendants
company = tree.root
headcounts = get_value(company, "headcount", PropagationMode.UP)
# [50, 15, 10, 30] - all values from subtree

# Get from a subtree
eng = tree.get("/company/eng")
eng_headcounts = get_value(eng, "headcount", PropagationMode.UP)
# [50, 15, 10] - only engineering subtree
```

!!! note "Result Type"
    UP propagation always returns a **list** of all values found in the subtree, including the resource itself if it has the attribute.

### When to Use UP

- **Rollup metrics** (headcount, budget, resource usage)
- **Collecting tags or labels** from children
- **Auditing** what values exist in a subtree
- **Validation** to ensure all children have required values

## MERGE_DOWN - Deep Dictionary Merge

Recursively merge dictionaries from ancestors. Child values override parent values at each key level.

```python
tree = ResourceTree(root_name="platform")

tree.root.set_attribute("config", {
    "database": {
        "host": "localhost",
        "port": 5432,
        "pool_size": 10
    },
    "cache": {
        "enabled": True,
        "ttl": 300
    }
})

tree.create("/platform/prod", attributes={
    "config": {
        "database": {
            "host": "prod.db.internal",
            "pool_size": 50
        }
    }
})

prod = tree.get("/platform/prod")
config = get_value(prod, "config", PropagationMode.MERGE_DOWN)
# {
#     "database": {
#         "host": "prod.db.internal",  # overridden
#         "port": 5432,                 # inherited
#         "pool_size": 50               # overridden
#     },
#     "cache": {
#         "enabled": True,              # inherited
#         "ttl": 300                    # inherited
#     }
# }
```

### Merge Rules

1. Child values override parent values for the same key
2. Merge happens recursively for nested dicts
3. Non-dict values are not merged (child wins completely)
4. New keys from child are added

### When to Use MERGE_DOWN

- **Complex configuration objects** with many nested settings
- **Layered overrides** where children customize parts of a structure
- **Feature configurations** with many options

## NONE - Local Only

Return only the value set directly on the resource. No inheritance, no aggregation.

```python
tree = ResourceTree(root_name="org")
tree.root.set_attribute("global_id", "ORG-001")

tree.create("/org/team")

team = tree.get("/org/team")

# NONE returns only local value
local = get_value(team, "global_id", PropagationMode.NONE)
# None - not set on this resource

# DOWN would inherit
inherited = get_value(team, "global_id", PropagationMode.DOWN)
# "ORG-001" - inherited from root
```

### When to Use NONE

- **Checking if a value is explicitly set** on a specific resource
- **Avoiding unintended inheritance** for resource-specific values
- **Validation** to ensure required values are set locally

## Choosing the Right Mode

```mermaid
graph TD
    A[Need to resolve an attribute?] --> B{How should it flow?}
    B -->|Parent to child| C{Is it a dict?}
    B -->|Child to parent| D[Use UP]
    B -->|No flow needed| E[Use NONE]
    C -->|Yes, merge layers| F[Use MERGE_DOWN]
    C -->|No, or replace entirely| G[Use DOWN]
```

| Scenario | Recommended Mode |
|----------|-----------------|
| Default timeout for all services | DOWN |
| Environment name (prod/staging) | DOWN |
| Team-specific budget | NONE or DOWN |
| Total headcount across org | UP |
| Layered feature flags | MERGE_DOWN |
| Database connection config | MERGE_DOWN |
| Resource-specific identifier | NONE |
