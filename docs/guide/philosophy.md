# Philosophy & Scope

HRCP is intentionally minimal: **~2000 lines of dependency-free Python** solving hierarchical configuration with provenance—nothing more.

## Core Focus

- **Inheritance (DOWN)**: Set defaults at the top, override at any level
- **Aggregation (UP)**: Roll up values from children
- **Merge (MERGE_DOWN)**: Combine dictionaries/lists hierarchically
- **Traceability**: Always know where a value came from

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
