# Kubernetes-Style Namespaces

Model Kubernetes namespaces with inherited resource quotas and limits.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="cluster")

# Cluster-wide defaults
tree.root.set_attribute("resource_quota", {
    "cpu": "100",
    "memory": "100Gi",
    "pods": 1000
})
tree.root.set_attribute("limit_range", {
    "default_cpu": "100m",
    "default_memory": "128Mi",
    "max_cpu": "2",
    "max_memory": "4Gi"
})
tree.root.set_attribute("network_policy", "deny-all")

# Production namespace with higher limits
tree.create("/cluster/prod", attributes={
    "resource_quota": {
        "cpu": "500",
        "memory": "500Gi",
        "pods": 5000
    },
    "limit_range": {
        "max_cpu": "8",
        "max_memory": "32Gi"
    }
})

# Development namespace with lower limits
tree.create("/cluster/dev", attributes={
    "resource_quota": {
        "cpu": "50",
        "memory": "50Gi",
        "pods": 500
    },
    "network_policy": "allow-all"
})

# Team namespaces inherit from their environment
tree.create("/cluster/prod/team-api")
tree.create("/cluster/prod/team-data")
tree.create("/cluster/dev/team-api")

def get_namespace_config(tree, namespace_path):
    """Get effective configuration for a namespace."""
    ns = tree.get(namespace_path)
    if not ns:
        return None

    return {
        "quota": get_value(ns, "resource_quota", PropagationMode.MERGE_DOWN),
        "limits": get_value(ns, "limit_range", PropagationMode.MERGE_DOWN),
        "network": get_value(ns, "network_policy", PropagationMode.DOWN),
    }

# Compare prod vs dev team-api namespaces
prod_config = get_namespace_config(tree, "/cluster/prod/team-api")
dev_config = get_namespace_config(tree, "/cluster/dev/team-api")

print("Production team-api:")
print(f"  CPU quota: {prod_config['quota']['cpu']}")      # 500
print(f"  Max CPU: {prod_config['limits']['max_cpu']}")   # 8
print(f"  Network: {prod_config['network']}")             # deny-all

print("\nDevelopment team-api:")
print(f"  CPU quota: {dev_config['quota']['cpu']}")       # 50
print(f"  Max CPU: {dev_config['limits']['max_cpu']}")    # 2 (inherited from cluster)
print(f"  Network: {dev_config['network']}")              # allow-all
```

## Key Patterns

- **Cluster defaults** apply to all namespaces
- **Environment overrides** (prod/dev) customize resource limits
- **Team namespaces** inherit from their environment
- **MERGE_DOWN** for quotas and limits allows partial overrides
- **DOWN** for network policy uses closest ancestor's value
