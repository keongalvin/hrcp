# Configuration Audit Report

Generate an audit report showing where values come from across the tree.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="services")

# Set up services with inherited and local values
tree.root.set_attribute("env", "prod")
tree.root.set_attribute("timeout", 30)
tree.create("/services/api", attributes={"port": 8080, "replicas": 3})
tree.create("/services/worker", attributes={"replicas": 5})
tree.create("/services/cache", attributes={"port": 6379, "timeout": 60})

def audit_report(tree, attrs):
    """Generate an audit report showing value provenance."""
    print("Configuration Audit Report")
    print("=" * 60)

    for resource in tree.query("/**"):
        print(f"\n{resource.path}")

        for attr in attrs:
            prov = get_value(resource, attr, PropagationMode.INHERIT, with_provenance=True)
            if prov is not None:
                source = "(local)" if prov.source_path == resource.path else f"(from {prov.source_path})"
                print(f"  {attr}: {prov.value} {source}")
            else:
                print(f"  {attr}: not set")

audit_report(tree, ["env", "port", "replicas", "timeout"])
```

## Output

```
Configuration Audit Report
============================================================

/services
  env: prod (local)
  port: not set
  replicas: not set
  timeout: 30 (local)

/services/api
  env: prod (from /services)
  port: 8080 (local)
  replicas: 3 (local)
  timeout: 30 (from /services)

/services/worker
  env: prod (from /services)
  port: not set
  replicas: 5 (local)
  timeout: 30 (from /services)

/services/cache
  env: prod (from /services)
  port: 6379 (local)
  replicas: not set
  timeout: 60 (local)
```

## Enhanced Audit with Diff

Compare configuration between environments:

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

## Key Patterns

- **Wildcard queries** (`/**`) to iterate all resources
- **Provenance tracking** shows local vs inherited
- **Audit utilities** for compliance and debugging
- **Diff reports** for comparing environments
