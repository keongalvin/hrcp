# Core Concepts

HRCP is built around a few key concepts that work together to provide hierarchical configuration management.

## Resource Tree

The `ResourceTree` is the container for your entire hierarchy. It manages resources and their relationships.

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="platform")
```

Every tree has exactly one **root resource**, accessible via `tree.root`.

## Resources

A **Resource** is a node in the tree. Each resource has:

- A **name** (the last segment of its path)
- A **path** (its full location in the tree, like `/platform/us-east/api`)
- **Attributes** (key-value pairs)
- **Children** (other resources nested beneath it)
- A **parent** (except for the root)

```python
# Create a resource
tree.create("/platform/us-east/api")

# Get a resource by path
api = tree.get("/platform/us-east/api")

# Access properties
print(api.name)      # "api"
print(api.path)      # "/platform/us-east/api"
print(api.parent)    # Resource at /platform/us-east
print(api.children)  # []
```

## Paths

Paths identify resources uniquely within a tree. They follow a filesystem-like convention:

- Paths start with `/`
- Segments are separated by `/`
- The root path is `/{root_name}`

```python
tree = ResourceTree(root_name="org")

# These are all valid paths:
"/org"                    # The root
"/org/team"               # Direct child of root
"/org/team/project"       # Nested resource
"/org/team/project/env"   # Deeply nested
```

!!! tip "Automatic Parent Creation"
    When you create a resource, HRCP automatically creates any missing parent resources:
    ```python
    tree.create("/org/team/project/env")
    # Also creates /org/team and /org/team/project if they don't exist
    ```

## Attributes

Attributes are the configuration values stored on resources:

```python
resource = tree.get("/org/team")

# Set attributes
resource.set_attribute("budget", 50000)
resource.set_attribute("tier", "premium")
resource.set_attribute("config", {"debug": True})

# Get local attribute (only what's set on this resource)
budget = resource.get_attribute("budget")  # 50000
missing = resource.get_attribute("unknown")  # None
```

Attributes can be any JSON-serializable value: strings, numbers, booleans, lists, or dicts.

## Propagation

**Propagation** determines how attribute values flow through the tree. This is the core feature that makes hierarchical configuration powerful.

See [Propagation Modes](propagation.md) for details.

```python
from hrcp import PropagationMode, get_effective_value

# DOWN: Inherit from ancestors
value = get_effective_value(resource, "timeout", PropagationMode.DOWN)

# UP: Aggregate from descendants  
values = get_effective_value(resource, "headcount", PropagationMode.UP)

# MERGE_DOWN: Deep-merge dicts from ancestors
config = get_effective_value(resource, "config", PropagationMode.MERGE_DOWN)

# NONE: Local value only
local = get_effective_value(resource, "name", PropagationMode.NONE)
```

## Provenance

**Provenance** tells you where a value came from. This is essential for debugging and auditing.

See [Provenance](provenance.md) for details.

```python
from hrcp import get_value_with_provenance

prov = get_value_with_provenance(resource, "timeout", PropagationMode.DOWN)
print(prov.value)        # The resolved value
print(prov.source_path)  # Which resource provided it
print(prov.mode)         # Which propagation mode was used
```

## Putting It Together

Here's how all concepts work together:

```python
from hrcp import (
    ResourceTree,
    PropagationMode,
    get_effective_value,
    get_value_with_provenance,
)

# 1. Create a tree
tree = ResourceTree(root_name="company")

# 2. Set attributes at different levels
tree.root.set_attribute("env", "production")
tree.root.set_attribute("log_level", "INFO")

# 3. Create resources with overrides
tree.create("/company/engineering", attributes={"log_level": "DEBUG"})
tree.create("/company/engineering/api")

# 4. Query with propagation
api = tree.get("/company/engineering/api")

env = get_effective_value(api, "env", PropagationMode.DOWN)
# "production" - inherited from root

log_level = get_effective_value(api, "log_level", PropagationMode.DOWN)
# "DEBUG" - inherited from /company/engineering (closest ancestor)

# 5. Track provenance
prov = get_value_with_provenance(api, "log_level", PropagationMode.DOWN)
print(f"{prov.value} from {prov.source_path}")
# "DEBUG from /company/engineering"
```
