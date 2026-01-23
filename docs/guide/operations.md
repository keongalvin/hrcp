# Tree Operations

HRCP provides powerful operations for manipulating trees and resources: cloning, merging, copying, moving, and renaming.

## Cloning

### Clone Entire Tree

Create an independent deep copy of the entire tree:

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="platform")
tree.root.set_attribute("env", "prod")
tree.create("/platform/api", attributes={"port": 8080})
tree.create("/platform/db", attributes={"host": "localhost"})

# Create a deep copy
cloned = tree.clone()

# Modify the original - clone is unaffected
tree.root.set_attribute("env", "staging")
tree.create("/platform/cache")

print(cloned.root.get_attribute("env"))  # "prod" (unchanged)
print(cloned.get("/platform/cache"))     # None (not in clone)
```

### Clone Subtree

Extract a subtree as a new independent tree:

```python
tree = ResourceTree(root_name="org")
tree.create("/org/engineering/platform", attributes={"budget": 100000})
tree.create("/org/engineering/mobile", attributes={"budget": 50000})
tree.create("/org/sales", attributes={"budget": 200000})

# Clone just the engineering subtree
eng_tree = tree.clone_subtree("/org/engineering")

# eng_tree has "engineering" as its root
print(eng_tree.root.name)  # "engineering"
print(eng_tree.get("/engineering/platform").get_attribute("budget"))  # 100000

# Original tree unchanged
print(tree.get("/org/sales").get_attribute("budget"))  # 200000
```

**Use cases for subtree cloning:**

- Extract team configurations for independent management
- Create environment-specific configuration subsets
- Backup specific portions of a configuration tree

## Merging Trees

Combine two trees by merging resources and attributes:

```python
# Base configuration
base = ResourceTree(root_name="config")
base.root.set_attribute("version", "1.0")
base.root.set_attribute("debug", False)
base.create("/config/api", attributes={"port": 8080})

# Override configuration
overrides = ResourceTree(root_name="config")
overrides.root.set_attribute("debug", True)
overrides.create("/config/api", attributes={"port": 9000, "ssl": True})
overrides.create("/config/cache", attributes={"ttl": 300})

# Merge overrides into base
base.merge(overrides)

# Existing attributes are updated
print(base.root.get_attribute("debug"))  # True (from overrides)
print(base.root.get_attribute("version"))  # "1.0" (preserved)

# Child attributes are merged
api = base.get("/config/api")
print(api.get_attribute("port"))  # 9000 (updated)
print(api.get_attribute("ssl"))   # True (added)

# New resources are added
print(base.get("/config/cache").get_attribute("ttl"))  # 300
```

### Environment Layering with Merge

A common pattern is layering environment-specific configs:

```python
def load_config(environment: str) -> ResourceTree:
    """Load base config and merge environment-specific overrides."""
    # Load base configuration
    base = ResourceTree.from_yaml_file("config/base.yaml")

    # Merge environment-specific overrides
    env_file = f"config/{environment}.yaml"
    try:
        env_config = ResourceTree.from_yaml_file(env_file)
        base.merge(env_config)
    except FileNotFoundError:
        pass  # No environment-specific config

    return base

# Usage
prod_config = load_config("production")
dev_config = load_config("development")
```

### Multi-Source Configuration

Merge configurations from multiple sources:

```python
def load_multi_source_config() -> ResourceTree:
    """Load and merge configs from multiple sources."""
    # Start with defaults
    config = ResourceTree(root_name="app")
    config.root.set_attribute("log_level", "INFO")
    config.root.set_attribute("timeout", 30)

    # Merge file config
    if os.path.exists("config.yaml"):
        file_config = ResourceTree.from_yaml_file("config.yaml")
        config.merge(file_config)

    # Merge environment overrides (highest priority)
    env_config = ResourceTree(root_name="app")
    if os.environ.get("LOG_LEVEL"):
        env_config.root.set_attribute("log_level", os.environ["LOG_LEVEL"])
    if os.environ.get("TIMEOUT"):
        env_config.root.set_attribute("timeout", int(os.environ["TIMEOUT"]))
    config.merge(env_config)

    return config
```

## Copying Resources

Copy a resource (and its subtree) to a new location within the same tree:

```python
tree = ResourceTree(root_name="services")
tree.create("/services/api-v1", attributes={
    "port": 8080,
    "version": "1.0",
    "config": {"debug": False}
})
tree.create("/services/api-v1/health", attributes={"path": "/health"})

# Copy to create v2 (with all children)
tree.copy("/services/api-v1", "/services/api-v2")

# Both exist, with independent copies of attributes
v1 = tree.get("/services/api-v1")
v2 = tree.get("/services/api-v2")

print(v1.get_attribute("port"))  # 8080
print(v2.get_attribute("port"))  # 8080

# Modify v2 independently
v2.set_attribute("port", 8081)
v2.set_attribute("version", "2.0")

print(v1.get_attribute("port"))  # 8080 (unchanged)
print(v2.get_attribute("port"))  # 8081

# Children are also copied
print(tree.get("/services/api-v2/health").get_attribute("path"))  # "/health"
```

### Copy for Templates

Use copy to create resources from templates:

```python
def create_service_from_template(tree, template_path, new_name, overrides=None):
    """Create a new service by copying a template."""
    parent = "/".join(template_path.rsplit("/", 1)[:-1]) or tree.root.path
    new_path = f"{parent}/{new_name}"

    tree.copy(template_path, new_path)

    if overrides:
        resource = tree.get(new_path)
        for key, value in overrides.items():
            resource.set_attribute(key, value)

    return new_path

# Setup template
tree = ResourceTree(root_name="services")
tree.create("/services/_template", attributes={
    "replicas": 1,
    "port": 8080,
    "health_check": "/health",
    "timeout": 30
})

# Create services from template
create_service_from_template(tree, "/services/_template", "api", {"port": 8080, "replicas": 3})
create_service_from_template(tree, "/services/_template", "worker", {"port": 8081})
create_service_from_template(tree, "/services/_template", "scheduler", {"port": 8082, "replicas": 1})
```

## Moving Resources

Move a resource (and its subtree) to a new location:

```python
tree = ResourceTree(root_name="org")
tree.create("/org/old-team/alice", attributes={"role": "developer"})
tree.create("/org/old-team/bob", attributes={"role": "designer"})
tree.create("/org/new-team")

# Move alice to new team
tree.move("/org/old-team/alice", "/org/new-team/alice")

# alice no longer in old team
print(tree.get("/org/old-team/alice"))  # None

# alice now in new team with all attributes
alice = tree.get("/org/new-team/alice")
print(alice.get_attribute("role"))  # "developer"
```

### Restructuring Hierarchies

Move is useful for reorganizing:

```python
tree = ResourceTree(root_name="platform")
tree.create("/platform/monolith/api", attributes={"type": "rest"})
tree.create("/platform/monolith/db", attributes={"type": "postgres"})
tree.create("/platform/monolith/cache", attributes={"type": "redis"})

# Restructure into microservices
tree.create("/platform/microservices")
tree.move("/platform/monolith/api", "/platform/microservices/api-service")
tree.move("/platform/monolith/cache", "/platform/microservices/cache-service")

# db stays in monolith, others moved
print(tree.get("/platform/monolith/api"))  # None
print(tree.get("/platform/microservices/api-service").get_attribute("type"))  # "rest"
```

## Renaming Resources

Rename a resource in place (keeping it under the same parent):

```python
tree = ResourceTree(root_name="config")
tree.create("/config/old-api", attributes={"port": 8080})

# Rename
tree.rename("/config/old-api", "new-api")

# Old name gone, new name has all attributes
print(tree.get("/config/old-api"))  # None
print(tree.get("/config/new-api").get_attribute("port"))  # 8080
```

### Rename for Versioning

```python
def version_bump(tree, service_path):
    """Rename current to -old, create new version."""
    resource = tree.get(service_path)
    if not resource:
        raise KeyError(f"Service not found: {service_path}")

    old_path = f"{service_path}-old"

    # Move current to -old (backup)
    tree.copy(service_path, old_path)

    # Clear attributes on original for fresh start
    for key in list(resource.attributes.keys()):
        resource.delete_attribute(key)

    return old_path

# Usage
tree = ResourceTree(root_name="services")
tree.create("/services/api", attributes={"version": "1.0", "port": 8080})

backup_path = version_bump(tree, "/services/api")
tree.get("/services/api").set_attribute("version", "2.0")

print(tree.get(backup_path).get_attribute("version"))  # "1.0"
print(tree.get("/services/api").get_attribute("version"))  # "2.0"
```

## Deleting Resources

Remove a resource and all its children:

```python
tree = ResourceTree(root_name="org")
tree.create("/org/team/alice")
tree.create("/org/team/bob")
tree.create("/org/config")

# Delete entire team (including all members)
tree.delete("/org/team")

print(tree.get("/org/team"))  # None
print(tree.get("/org/team/alice"))  # None
print(tree.get("/org/config"))  # Still exists
```

### Safe Deletion with Checks

```python
def safe_delete(tree, path, require_empty=False):
    """Delete resource with safety checks."""
    resource = tree.get(path)
    if not resource:
        return False

    if require_empty and resource.children:
        raise ValueError(f"Cannot delete {path}: has {len(resource.children)} children")

    tree.delete(path)
    return True

# Usage
tree = ResourceTree(root_name="org")
tree.create("/org/team/alice")

# This will raise because team has children
try:
    safe_delete(tree, "/org/team", require_empty=True)
except ValueError as e:
    print(e)  # "Cannot delete /org/team: has 1 children"

# This works
safe_delete(tree, "/org/team/alice", require_empty=True)
safe_delete(tree, "/org/team", require_empty=True)
```

## Walking the Tree

Iterate over all resources:

```python
tree = ResourceTree(root_name="org")
tree.create("/org/eng/alice", attributes={"role": "dev"})
tree.create("/org/eng/bob", attributes={"role": "qa"})
tree.create("/org/sales/carol", attributes={"role": "sales"})

# Walk all resources
for resource in tree.walk():
    print(f"{resource.path}: {dict(resource.attributes)}")
# /org: {}
# /org/eng: {}
# /org/eng/alice: {'role': 'dev'}
# /org/eng/bob: {'role': 'qa'}
# /org/sales: {}
# /org/sales/carol: {'role': 'sales'}

# Walk subtree only
for resource in tree.walk("/org/eng"):
    print(resource.path)
# /org/eng
# /org/eng/alice
# /org/eng/bob
```

## Tree Inspection

### Count Resources

```python
tree = ResourceTree(root_name="platform")
tree.create("/platform/api")
tree.create("/platform/db")
tree.create("/platform/cache")

print(len(tree))  # 4 (root + 3 children)
```
