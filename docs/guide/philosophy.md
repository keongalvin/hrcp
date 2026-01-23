# Philosophy & Scope

HRCP is intentionally minimal: **~1200 lines of dependency-free Python** solving hierarchical configuration with provenance—nothing more.

## Core Focus

- **Inheritance (DOWN)**: Set defaults at the top, override at any level
- **Aggregation (UP)**: Roll up values from children
- **Merge (MERGE_DOWN)**: Combine dictionaries/lists hierarchically
- **Traceability**: Always know where a value came from

## DIY Patterns

These are trivial—we don't include them because they're one-liners.

### Search & Filter

```python
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
# clone tree
cloned = ResourceTree.from_dict(tree.to_dict())

# merge trees (source into target)
for r in source.walk():
    target_r = target.get(r.path) or target.create(r.path)
    for k, v in r.attributes.items():
        target_r.set_attribute(k, v)

# copy resource
data = tree.get(src).attributes.copy()
tree.create(dest, attributes=data)

# move resource
tree.create(dest, attributes=tree.get(src).attributes.copy())
tree.delete(src)
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
| Conditional Required (schema) | Too complex |

## Guidelines for New Features

Before adding a feature, ask:

1. Does it fit the core mission (hierarchical config + provenance)?
2. Can it be done in <100 lines?
3. Is it a library concern or application concern?
4. Does it require new dependencies?
5. Would users expect this in a "minimal" library?

**If in doubt, leave it out.** Users can build on top of HRCP.
