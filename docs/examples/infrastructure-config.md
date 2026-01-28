# Infrastructure Configuration

Model your cloud infrastructure with inherited settings.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="infra")

# Global defaults
tree.root.set_attribute("region", "us-east-1")
tree.root.set_attribute("instance_type", "t3.medium")
tree.root.set_attribute("monitoring", {
    "enabled": True,
    "interval": 60,
    "alerts": True
})

# Production environment
tree.create("/infra/prod", attributes={
    "instance_type": "t3.large",
    "monitoring": {
        "interval": 30  # More frequent in prod
    }
})

# Production services
tree.create("/infra/prod/api", attributes={
    "replicas": 5,
    "port": 443
})
tree.create("/infra/prod/worker", attributes={
    "replicas": 10
})
tree.create("/infra/prod/cache", attributes={
    "instance_type": "r5.xlarge",  # Memory optimized
    "replicas": 3
})

# Staging environment
tree.create("/infra/staging", attributes={
    "monitoring": {
        "alerts": False  # No alerts in staging
    }
})
tree.create("/infra/staging/api", attributes={
    "replicas": 1,
    "port": 8443
})

# Query with provenance
api = tree.get("/infra/prod/api")
prov = get_value(api, "instance_type", PropagationMode.INHERIT, with_provenance=True)
print(f"Instance type: {prov.value} (from {prov.source_path})")
# Instance type: t3.large (from /infra/prod)
```

## Key Patterns

- **Environment separation** (prod/staging) with different defaults
- **Service-specific overrides** for replicas, ports, instance types
- **MERGE** for monitoring config allows partial customization
- **Provenance tracking** shows which level defined each setting
