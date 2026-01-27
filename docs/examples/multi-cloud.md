# Multi-Cloud Infrastructure

Manage configuration across multiple cloud providers.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="infrastructure")

# Global defaults
tree.root.set_attribute("monitoring", {"enabled": True, "interval": 60})
tree.root.set_attribute("backup", {"enabled": True, "retention_days": 30})
tree.root.set_attribute("tags", {"managed_by": "terraform", "team": "platform"})

# AWS configuration
tree.create("/infrastructure/aws", attributes={
    "provider": "aws",
    "default_region": "us-east-1",
    "tags": {"cloud": "aws"}
})

tree.create("/infrastructure/aws/prod", attributes={
    "vpc_cidr": "10.0.0.0/16",
    "tags": {"environment": "production"}
})
tree.create("/infrastructure/aws/prod/api", attributes={
    "instance_type": "t3.large",
    "min_instances": 3,
    "max_instances": 10
})

# GCP configuration
tree.create("/infrastructure/gcp", attributes={
    "provider": "gcp",
    "default_region": "us-central1",
    "tags": {"cloud": "gcp"}
})

tree.create("/infrastructure/gcp/prod", attributes={
    "vpc_cidr": "10.1.0.0/16",
    "tags": {"environment": "production"}
})
tree.create("/infrastructure/gcp/prod/api", attributes={
    "machine_type": "n1-standard-2",
    "min_instances": 2,
    "max_instances": 8
})

def get_infra_config(tree, path):
    """Get full infrastructure configuration with merged tags."""
    resource = tree.get(path)
    return {
        "provider": get_value(resource, "provider", PropagationMode.DOWN),
        "region": get_value(resource, "default_region", PropagationMode.DOWN),
        "tags": get_value(resource, "tags", PropagationMode.MERGE_DOWN),
        "monitoring": get_value(resource, "monitoring", PropagationMode.MERGE_DOWN),
        "backup": get_value(resource, "backup", PropagationMode.MERGE_DOWN),
    }

# Compare AWS vs GCP prod API configs
aws_config = get_infra_config(tree, "/infrastructure/aws/prod/api")
gcp_config = get_infra_config(tree, "/infrastructure/gcp/prod/api")

print("AWS API Tags:", aws_config["tags"])
# {'managed_by': 'terraform', 'team': 'platform', 'cloud': 'aws', 'environment': 'production'}

print("GCP API Tags:", gcp_config["tags"])
# {'managed_by': 'terraform', 'team': 'platform', 'cloud': 'gcp', 'environment': 'production'}
```

## Key Patterns

- **Global defaults** (monitoring, backup, base tags) at root
- **Provider-specific settings** under each cloud
- **Environment separation** within each provider
- **Tag merging** accumulates tags through the hierarchy
- **Consistent interface** via `get_infra_config()` regardless of provider
