# Search and Filter

HRCP provides powerful methods for finding resources by attribute values, predicates, or patterns.

## Finding Resources by Attributes

### Find All Matches

Use `find()` to get all resources with matching attribute values:

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="org")
tree.create("/org/alice", attributes={"role": "developer", "team": "backend"})
tree.create("/org/bob", attributes={"role": "developer", "team": "frontend"})
tree.create("/org/carol", attributes={"role": "manager", "team": "backend"})
tree.create("/org/dan", attributes={"role": "developer", "team": "backend"})

# Find all developers
developers = tree.find(role="developer")
print([r.name for r in developers])  # ['alice', 'bob', 'dan']

# Find by multiple attributes (AND logic)
backend_devs = tree.find(role="developer", team="backend")
print([r.name for r in backend_devs])  # ['alice', 'dan']
```

### Find First Match

Use `find_first()` when you only need one result:

```python
# Find first manager
manager = tree.find_first(role="manager")
print(manager.name)  # 'carol'

# Returns None if no match
admin = tree.find_first(role="admin")
print(admin)  # None
```

### Search Within Subtree

Restrict search to a specific subtree:

```python
tree = ResourceTree(root_name="company")
tree.create("/company/engineering/alice", attributes={"level": "senior"})
tree.create("/company/engineering/bob", attributes={"level": "junior"})
tree.create("/company/sales/carol", attributes={"level": "senior"})

# Find seniors only in engineering
eng_seniors = tree.find(level="senior", path="/company/engineering")
print([r.name for r in eng_seniors])  # ['alice']
```

## Filtering with Predicates

For complex conditions, use `filter()` with a predicate function:

```python
tree = ResourceTree(root_name="services")
tree.create("/services/api", attributes={"replicas": 3, "memory": 512})
tree.create("/services/worker", attributes={"replicas": 10, "memory": 1024})
tree.create("/services/scheduler", attributes={"replicas": 1, "memory": 256})

# Find services with more than 2 replicas
high_replica = tree.filter(lambda r: r.attributes.get("replicas", 0) > 2)
print([r.name for r in high_replica])  # ['api', 'worker']

# Find services using significant memory
memory_heavy = tree.filter(lambda r: r.attributes.get("memory", 0) >= 512)
print([r.name for r in memory_heavy])  # ['api', 'worker']

# Complex conditions
critical = tree.filter(
    lambda r: r.attributes.get("replicas", 0) >= 3 
              and r.attributes.get("memory", 0) >= 512
)
print([r.name for r in critical])  # ['api', 'worker']
```

### Filter with Path Restriction

```python
tree = ResourceTree(root_name="platform")
tree.create("/platform/prod/api", attributes={"healthy": True})
tree.create("/platform/prod/db", attributes={"healthy": False})
tree.create("/platform/staging/api", attributes={"healthy": True})

# Find unhealthy services in production only
unhealthy_prod = tree.filter(
    lambda r: r.attributes.get("healthy") is False,
    path="/platform/prod"
)
print([r.name for r in unhealthy_prod])  # ['db']
```

## Checking Existence

Use `exists()` to check if any matching resource exists:

```python
tree = ResourceTree(root_name="features")
tree.create("/features/dark-mode", attributes={"enabled": True})
tree.create("/features/new-checkout", attributes={"enabled": False})

# Check if any feature is enabled
has_enabled = tree.exists(enabled=True)
print(has_enabled)  # True

# Check for specific feature
has_beta = tree.exists(name="beta-feature")
print(has_beta)  # False
```

### Validation with exists()

```python
def validate_required_services(tree, required):
    """Check that all required services exist."""
    missing = []
    for service_type in required:
        if not tree.exists(type=service_type):
            missing.append(service_type)
    return missing

tree = ResourceTree(root_name="infra")
tree.create("/infra/api", attributes={"type": "api"})
tree.create("/infra/db", attributes={"type": "database"})

missing = validate_required_services(tree, ["api", "database", "cache"])
print(missing)  # ['cache']
```

## Counting Resources

Use `count()` to count matching resources:

```python
tree = ResourceTree(root_name="org")
tree.create("/org/eng/alice", attributes={"role": "developer"})
tree.create("/org/eng/bob", attributes={"role": "developer"})
tree.create("/org/eng/carol", attributes={"role": "manager"})
tree.create("/org/sales/dan", attributes={"role": "sales"})
tree.create("/org/sales/eve", attributes={"role": "sales"})

# Count by role
print(tree.count(role="developer"))  # 2
print(tree.count(role="manager"))    # 1
print(tree.count(role="sales"))      # 2
print(tree.count(role="intern"))     # 0
```

### Statistics with count()

```python
def org_stats(tree):
    """Generate organization statistics."""
    return {
        "total": len(tree),
        "developers": tree.count(role="developer"),
        "managers": tree.count(role="manager"),
        "active": tree.count(status="active"),
        "on_leave": tree.count(status="on_leave"),
    }

stats = org_stats(tree)
print(stats)
# {'total': 6, 'developers': 2, 'managers': 1, 'active': 0, 'on_leave': 0}
```

## Practical Patterns

### Service Discovery

```python
def discover_services(tree, service_type, environment=None):
    """Discover services by type, optionally filtered by environment."""
    if environment:
        return tree.find(type=service_type, env=environment)
    return tree.find(type=service_type)

def get_service_endpoints(tree, service_type):
    """Get all endpoints for a service type."""
    services = discover_services(tree, service_type)
    endpoints = []
    for service in services:
        host = service.get_attribute("host")
        port = service.get_attribute("port")
        if host and port:
            endpoints.append(f"{host}:{port}")
    return endpoints

# Setup
tree = ResourceTree(root_name="platform")
tree.create("/platform/prod/api-1", attributes={
    "type": "api", "env": "prod", "host": "api1.example.com", "port": 8080
})
tree.create("/platform/prod/api-2", attributes={
    "type": "api", "env": "prod", "host": "api2.example.com", "port": 8080
})
tree.create("/platform/staging/api", attributes={
    "type": "api", "env": "staging", "host": "staging.example.com", "port": 8080
})

# Discover all API endpoints
all_apis = get_service_endpoints(tree, "api")
print(all_apis)
# ['api1.example.com:8080', 'api2.example.com:8080', 'staging.example.com:8080']

# Discover production APIs only
prod_apis = discover_services(tree, "api", "prod")
print([s.name for s in prod_apis])  # ['api-1', 'api-2']
```

### Health Monitoring

```python
def get_health_report(tree, path=None):
    """Generate health report for services."""
    healthy = tree.filter(
        lambda r: r.attributes.get("health_status") == "healthy",
        path=path
    )
    unhealthy = tree.filter(
        lambda r: r.attributes.get("health_status") == "unhealthy",
        path=path
    )
    unknown = tree.filter(
        lambda r: r.attributes.get("health_status") is None 
                  and r.attributes.get("type") == "service",
        path=path
    )
    
    return {
        "healthy": [r.path for r in healthy],
        "unhealthy": [r.path for r in unhealthy],
        "unknown": [r.path for r in unknown],
        "summary": {
            "healthy": len(healthy),
            "unhealthy": len(unhealthy),
            "unknown": len(unknown),
        }
    }

# Setup
tree = ResourceTree(root_name="platform")
tree.create("/platform/api", attributes={"type": "service", "health_status": "healthy"})
tree.create("/platform/db", attributes={"type": "service", "health_status": "unhealthy"})
tree.create("/platform/cache", attributes={"type": "service"})  # No health status

report = get_health_report(tree)
print(report["summary"])
# {'healthy': 1, 'unhealthy': 1, 'unknown': 1}
```

### Resource Allocation

```python
def find_available_capacity(tree, required_memory, required_cpu):
    """Find nodes with sufficient available capacity."""
    return tree.filter(
        lambda r: (
            r.attributes.get("type") == "node"
            and r.attributes.get("available_memory", 0) >= required_memory
            and r.attributes.get("available_cpu", 0) >= required_cpu
        )
    )

def total_capacity(tree):
    """Calculate total cluster capacity."""
    nodes = tree.find(type="node")
    return {
        "total_memory": sum(n.attributes.get("total_memory", 0) for n in nodes),
        "total_cpu": sum(n.attributes.get("total_cpu", 0) for n in nodes),
        "node_count": len(nodes),
    }

# Setup
tree = ResourceTree(root_name="cluster")
tree.create("/cluster/node-1", attributes={
    "type": "node", "total_memory": 16000, "available_memory": 8000,
    "total_cpu": 8, "available_cpu": 4
})
tree.create("/cluster/node-2", attributes={
    "type": "node", "total_memory": 32000, "available_memory": 16000,
    "total_cpu": 16, "available_cpu": 10
})
tree.create("/cluster/node-3", attributes={
    "type": "node", "total_memory": 16000, "available_memory": 2000,
    "total_cpu": 8, "available_cpu": 1
})

# Find nodes that can run a 4GB, 2 CPU workload
available = find_available_capacity(tree, 4000, 2)
print([n.name for n in available])  # ['node-1', 'node-2']

# Get total capacity
print(total_capacity(tree))
# {'total_memory': 64000, 'total_cpu': 32, 'node_count': 3}
```

### Tag-Based Grouping

```python
def find_by_tag(tree, tag):
    """Find all resources with a specific tag."""
    return tree.filter(
        lambda r: tag in r.attributes.get("tags", [])
    )

def find_by_all_tags(tree, tags):
    """Find resources that have ALL specified tags."""
    return tree.filter(
        lambda r: all(t in r.attributes.get("tags", []) for t in tags)
    )

def find_by_any_tag(tree, tags):
    """Find resources that have ANY of the specified tags."""
    return tree.filter(
        lambda r: any(t in r.attributes.get("tags", []) for t in tags)
    )

# Setup
tree = ResourceTree(root_name="services")
tree.create("/services/api", attributes={"tags": ["critical", "public", "rest"]})
tree.create("/services/db", attributes={"tags": ["critical", "internal"]})
tree.create("/services/worker", attributes={"tags": ["background", "internal"]})

# Find critical services
critical = find_by_tag(tree, "critical")
print([s.name for s in critical])  # ['api', 'db']

# Find services that are both critical AND internal
critical_internal = find_by_all_tags(tree, ["critical", "internal"])
print([s.name for s in critical_internal])  # ['db']

# Find services that are either public OR background
public_or_bg = find_by_any_tag(tree, ["public", "background"])
print([s.name for s in public_or_bg])  # ['api', 'worker']
```

### Audit and Compliance

```python
def audit_missing_attributes(tree, required_attrs, resource_type=None):
    """Find resources missing required attributes."""
    def is_missing(resource):
        # Optionally filter by type
        if resource_type and resource.attributes.get("type") != resource_type:
            return False
        # Check for missing attributes
        for attr in required_attrs:
            if resource.attributes.get(attr) is None:
                return True
        return False
    
    return tree.filter(is_missing)

def compliance_report(tree, rules):
    """
    Generate compliance report.
    
    rules = {
        "attribute_name": {"required": True, "type": str, "pattern": "..."}
    }
    """
    issues = []
    
    for resource in tree.walk():
        for attr, rule in rules.items():
            value = resource.attributes.get(attr)
            
            if rule.get("required") and value is None:
                issues.append({
                    "path": resource.path,
                    "attribute": attr,
                    "issue": "missing required attribute"
                })
            elif value is not None:
                if "type" in rule and not isinstance(value, rule["type"]):
                    issues.append({
                        "path": resource.path,
                        "attribute": attr,
                        "issue": f"expected {rule['type'].__name__}, got {type(value).__name__}"
                    })
    
    return issues

# Setup
tree = ResourceTree(root_name="services")
tree.create("/services/api", attributes={"owner": "team-a", "port": 8080})
tree.create("/services/db", attributes={"port": 5432})  # Missing owner
tree.create("/services/cache", attributes={"owner": "team-b"})  # Missing port

# Find services missing required attributes
missing = audit_missing_attributes(tree, ["owner", "port"])
print([r.path for r in missing])
# ['/services/db', '/services/cache']
```

## Combining Search with Propagation

Search results work seamlessly with propagation:

```python
from hrcp import get_value, PropagationMode

tree = ResourceTree(root_name="platform")
tree.root.set_attribute("timeout", 30)
tree.root.set_attribute("env", "prod")

tree.create("/platform/region-a/api", attributes={"type": "api", "timeout": 60})
tree.create("/platform/region-a/db", attributes={"type": "database"})
tree.create("/platform/region-b/api", attributes={"type": "api"})
tree.create("/platform/region-b/db", attributes={"type": "database", "timeout": 120})

# Find all API services and get their effective timeouts
apis = tree.find(type="api")
for api in apis:
    timeout = get_value(api, "timeout", PropagationMode.DOWN)
    print(f"{api.path}: timeout={timeout}")
# /platform/region-a/api: timeout=60 (local override)
# /platform/region-b/api: timeout=30 (inherited from root)
```
