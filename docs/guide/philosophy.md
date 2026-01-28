# Philosophy & Scope

HRCP is intentionally minimal: **~1000 lines of dependency-free Python** solving hierarchical configuration with provenance—nothing more.

## Core Focus

- **Inheritance (INHERIT)**: Set defaults at the top, override at any level
- **Aggregation (AGGREGATE)**: Roll up values from children
- **Merge (MERGE)**: Combine dictionaries hierarchically
- **Traceability**: Always know where a value came from

## DIY Patterns

These are trivial—we don't include them because they're one-liners.

### Search & Filter

```python
tree = ResourceTree(root_name="root")
tree.create("/root/prod", attributes={"env": "prod", "critical": True, "enabled": True})
tree.create("/root/staging", attributes={"env": "staging", "enabled": True})

# find by attribute
[r for r in tree.walk() if r.attributes.get("env") == "prod"]

# find first match
next((r for r in tree.walk() if r.attributes.get("env") == "prod"), None)

# exists / count
any(r.attributes.get("critical") for r in tree.walk())
sum(1 for r in tree.walk() if r.attributes.get("enabled"))

# all attribute keys
{k for r in tree.walk() for k in r.attributes}

# tree depth
def depth(r): return 1 if not r.children else 1 + max(depth(c) for c in r.children.values())
```

### Tree Operations

```python
tree = ResourceTree(root_name="root")
tree.create("/root/src", attributes={"key": "value"})
source = ResourceTree(root_name="root")
source.create("/root/item", attributes={"a": 1})
target = ResourceTree(root_name="root")

# clone tree
cloned = ResourceTree.from_dict(tree.to_dict())

# merge trees (source into target)
for r in source.walk():
    target_r = target.get(r.path) or target.create(r.path)
    for k, v in r.attributes.items():
        target_r.set_attribute(k, v)

# copy resource
data = tree.get("/root/src").attributes.copy()
tree.create("/root/dest", attributes=data)

# move resource (to new location)
tree.create("/root/moved", attributes=tree.get("/root/src").attributes.copy())
tree.delete("/root/src")
```

## Out of Scope

These features were considered but rejected as beyond the library's scope:

| Feature | Why Out of Scope |
|---------|------------------|
| Observers/Callbacks | Event-driven paradigm—application layer concern |
| History/Audit Log | Persistence concern—use a database |
| Undo/Redo | Application state management |
| Transactions with rollback | Database-level feature |
| Computed Attributes | Application logic—do externally |
| Environment Variable Interpolation | Application concern—preprocess before loading |
| Cross-Reference/Templates | String processing—use a separate library |
| Lazy Loading | Persistence/performance optimization |
| Async I/O | Different paradigm |
| Caching | Premature optimization |
| Advanced Filters (`__gt`, `__startswith`) | Over-engineering |
| Pagination | Application concern |
| INI/Dotenv formats | Format bloat |
| LATERAL propagation | Changes core model |
| Conditional Propagation | Too complex |
| Watch/Subscribe | Real-time is out of scope |
| Schema Validation | Too complex—use Pydantic/attrs externally |

## Thread Safety

HRCP is **not thread-safe** by design. This is intentional:

- Configuration is typically loaded at startup, not modified at runtime
- Thread-safe data structures add complexity and overhead
- Users who need concurrency can add their own synchronization

### Single-Threaded Usage (Recommended)

```python
tree = ResourceTree(root_name="app")
tree.root.set_attribute("timeout", 30)
resource = tree.create("/app/service")

# Use throughout application (read-only)
timeout = get_value(resource, "timeout", PropagationMode.INHERIT)
```

### Multi-Threaded Usage

If you need concurrent access:

```python
import threading

# Option 1: Read-only after initialization (safe)
tree = ResourceTree(root_name="app")
tree.create("/app/service", attributes={"timeout": 30})
# Multiple threads can safely read from tree

# Option 2: Lock for modifications
lock = threading.Lock()

def update_config(path, key, value):
    with lock:
        resource = tree.get(path)
        resource.set_attribute(key, value)

# Option 3: Copy-on-write pattern
def get_updated_tree(tree, path, key, value):
    new_tree = ResourceTree.from_dict(tree.to_dict())
    new_tree.get(path).set_attribute(key, value)
    return new_tree
```

### Async/Await

HRCP operations are synchronous. For async applications:

```python
import asyncio

def create_tree():
    tree = ResourceTree(root_name="app")
    tree.root.set_attribute("timeout", 30)
    return tree

async def load_config():
    # Run synchronous code in executor
    loop = asyncio.get_event_loop()
    tree = await loop.run_in_executor(None, create_tree)
    return tree
```

## Guidelines for New Features

Before adding a feature, ask:

1. Does it fit the core mission (hierarchical config + provenance)?
2. Can it be done in <100 lines?
3. Is it a library concern or application concern?
4. Does it require new dependencies?
5. Would users expect this in a "minimal" library?

**If in doubt, leave it out.** Users can build on top of HRCP.
