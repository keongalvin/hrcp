# GitOps Repository Configuration

Model a GitOps repository structure with environment promotion.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="gitops")

# Base application configuration
tree.root.set_attribute("image_policy", "always-pull")
tree.root.set_attribute("replicas", 1)
tree.root.set_attribute("resources", {
    "requests": {"cpu": "100m", "memory": "128Mi"},
    "limits": {"cpu": "500m", "memory": "512Mi"}
})

# Application definitions
apps = ["frontend", "backend", "worker"]
envs = ["dev", "staging", "prod"]

for app in apps:
    tree.create(f"/gitops/apps/{app}")
    for env in envs:
        tree.create(f"/gitops/apps/{app}/{env}")

# Environment-specific overrides
tree.get("/gitops/apps/frontend/prod").set_attribute("replicas", 3)
tree.get("/gitops/apps/backend/prod").set_attribute("replicas", 5)
tree.get("/gitops/apps/backend/prod").set_attribute("resources", {
    "requests": {"cpu": "500m", "memory": "1Gi"},
    "limits": {"cpu": "2", "memory": "4Gi"}
})
tree.get("/gitops/apps/worker/prod").set_attribute("replicas", 10)

# Staging gets 50% of prod
tree.get("/gitops/apps/frontend/staging").set_attribute("replicas", 2)
tree.get("/gitops/apps/backend/staging").set_attribute("replicas", 3)

def generate_manifest(tree, app, env):
    """Generate Kubernetes manifest values for an app in an environment."""
    path = f"/gitops/apps/{app}/{env}"
    resource = tree.get(path)

    return {
        "app": app,
        "environment": env,
        "replicas": get_value(resource, "replicas", PropagationMode.INHERIT),
        "image_policy": get_value(resource, "image_policy", PropagationMode.INHERIT),
        "resources": get_value(resource, "resources", PropagationMode.MERGE),
    }

# Generate manifests
for env in ["dev", "staging", "prod"]:
    manifest = generate_manifest(tree, "backend", env)
    print(f"{env}: replicas={manifest['replicas']}, cpu_limit={manifest['resources']['limits']['cpu']}")

# dev: replicas=1, cpu_limit=500m
# staging: replicas=3, cpu_limit=500m
# prod: replicas=5, cpu_limit=2
```

## Key Patterns

- **Base configuration** at root applies to all apps/environments
- **App structure** groups environments under each application
- **Environment promotion** (dev → staging → prod) with increasing resources
- **MERGE_DOWN** for resource specs allows partial overrides
