# Use Cases

Real-world examples of how HRCP solves hierarchical configuration problems.

## Multi-Tenant SaaS Platform

Manage configuration for a SaaS platform with organizations, tenants, and projects.

```python
from hrcp import ResourceTree, PropagationMode, get_effective_value

tree = ResourceTree(root_name="platform")

# Platform-wide defaults
tree.root.set_attribute("timeout", 30)
tree.root.set_attribute("max_requests_per_minute", 1000)
tree.root.set_attribute("features", {
    "dark_mode": False,
    "beta_features": False,
    "ai_assist": False
})

# Enterprise tenant with custom limits
tree.create("/platform/acme-corp", attributes={
    "tier": "enterprise",
    "max_requests_per_minute": 10000,
    "features": {
        "ai_assist": True
    }
})

# Projects inherit from tenant
tree.create("/platform/acme-corp/webapp")
tree.create("/platform/acme-corp/mobile-api")
tree.create("/platform/acme-corp/analytics", attributes={
    "timeout": 120  # Analytics needs more time
})

# Free tier tenant
tree.create("/platform/small-startup", attributes={
    "tier": "free",
    "max_requests_per_minute": 100
})
tree.create("/platform/small-startup/app")

# Query configuration
analytics = tree.get("/platform/acme-corp/analytics")

timeout = get_effective_value(analytics, "timeout", PropagationMode.DOWN)
# 120 (local override)

rate_limit = get_effective_value(analytics, "max_requests_per_minute", PropagationMode.DOWN)
# 10000 (from tenant)

features = get_effective_value(analytics, "features", PropagationMode.MERGE_DOWN)
# {"dark_mode": False, "beta_features": False, "ai_assist": True}
# ai_assist merged from tenant, others from platform
```

## Infrastructure Configuration

Model your cloud infrastructure with inherited settings.

```python
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
from hrcp import get_value_with_provenance

api = tree.get("/infra/prod/api")
prov = get_value_with_provenance(api, "instance_type", PropagationMode.DOWN)
print(f"Instance type: {prov.value} (from {prov.source_path})")
# Instance type: t3.large (from /infra/prod)
```

## Feature Flags

Implement feature flags with hierarchical rollout.

```python
tree = ResourceTree(root_name="features")

# Global feature states
tree.root.set_attribute("new_checkout", False)
tree.root.set_attribute("dark_mode", False)
tree.root.set_attribute("ai_suggestions", False)

# Beta users get early access
tree.create("/features/beta", attributes={
    "new_checkout": True,
    "dark_mode": True,
    "ai_suggestions": True
})

# Specific beta users
tree.create("/features/beta/user-123")
tree.create("/features/beta/user-456", attributes={
    "ai_suggestions": False  # Opted out
})

# Canary rollout (10% of users)
tree.create("/features/canary", attributes={
    "new_checkout": True
})

# Check features for a user
def get_user_features(tree, user_path):
    """Get all feature flags for a user."""
    user = tree.get(user_path)
    if not user:
        user = tree.root  # Default to global features
    
    return {
        "new_checkout": get_effective_value(user, "new_checkout", PropagationMode.DOWN),
        "dark_mode": get_effective_value(user, "dark_mode", PropagationMode.DOWN),
        "ai_suggestions": get_effective_value(user, "ai_suggestions", PropagationMode.DOWN),
    }

print(get_user_features(tree, "/features/beta/user-123"))
# {"new_checkout": True, "dark_mode": True, "ai_suggestions": True}

print(get_user_features(tree, "/features/beta/user-456"))
# {"new_checkout": True, "dark_mode": True, "ai_suggestions": False}

print(get_user_features(tree, "/features/canary/user-789"))
# {"new_checkout": True, "dark_mode": False, "ai_suggestions": False}
```

## Organization Budget Rollup

Aggregate budgets from teams up to the organization level.

```python
tree = ResourceTree(root_name="company")

# Teams with budgets
tree.create("/company/engineering", attributes={"budget": 500000})
tree.create("/company/engineering/platform", attributes={"budget": 200000})
tree.create("/company/engineering/mobile", attributes={"budget": 150000})
tree.create("/company/engineering/web", attributes={"budget": 150000})

tree.create("/company/sales", attributes={"budget": 300000})
tree.create("/company/sales/enterprise", attributes={"budget": 200000})
tree.create("/company/sales/smb", attributes={"budget": 100000})

tree.create("/company/marketing", attributes={"budget": 200000})

# Aggregate budgets upward
def get_total_budget(resource):
    """Get total budget for a resource and all descendants."""
    budgets = get_effective_value(resource, "budget", PropagationMode.UP)
    return sum(budgets) if budgets else 0

print(f"Engineering total: ${get_total_budget(tree.get('/company/engineering')):,}")
# Engineering total: $1,000,000

print(f"Company total: ${get_total_budget(tree.root):,}")
# Company total: $1,500,000
```

## Access Control Inheritance

Implement role-based access control with inherited permissions.

```python
tree = ResourceTree(root_name="org")

# Organization-level admins
tree.root.set_attribute("admins", ["alice@company.com"])
tree.root.set_attribute("viewers", [])

# Department permissions
tree.create("/org/engineering", attributes={
    "admins": ["bob@company.com"],
    "viewers": ["carol@company.com"]
})

tree.create("/org/engineering/secrets", attributes={
    "admins": [],  # No additional admins
    "viewers": []  # Explicitly restricted
})

# Get effective permissions (merge all admin lists)
def get_effective_admins(resource):
    """Get all admins with access to this resource."""
    admins_lists = get_effective_value(resource, "admins", PropagationMode.UP)
    # Flatten and dedupe
    all_admins = set()
    for admin_list in admins_lists or []:
        all_admins.update(admin_list)
    return list(all_admins)

# For DOWN propagation of permissions (cumulative)
def has_admin_access(resource, user):
    """Check if user has admin access via inheritance."""
    current = resource
    while current:
        admins = current.get_attribute("admins") or []
        if user in admins:
            return True
        current = current.parent
    return False

print(has_admin_access(tree.get("/org/engineering/secrets"), "alice@company.com"))
# True (org admin)

print(has_admin_access(tree.get("/org/engineering/secrets"), "bob@company.com"))
# True (engineering admin)

print(has_admin_access(tree.get("/org/engineering/secrets"), "carol@company.com"))
# False (only viewer)
```

## Configuration Validation Report

Generate a validation report for all resources.

```python
from hrcp import get_value_with_provenance

tree = ResourceTree(root_name="services")

# Define schemas
tree.define("port", type_=int, ge=1, le=65535)
tree.define("replicas", type_=int, ge=1, le=100)
tree.define("env", choices=("dev", "staging", "prod"))

# Set up services
tree.root.set_attribute("env", "prod")
tree.create("/services/api", attributes={"port": 8080, "replicas": 3})
tree.create("/services/worker", attributes={"replicas": 5})
tree.create("/services/cache", attributes={"port": 6379})

def validation_report(tree, required_attrs):
    """Generate a validation report."""
    print("Configuration Validation Report")
    print("=" * 60)
    
    for resource in tree.query("/**"):
        issues = []
        
        for attr in required_attrs:
            prov = get_value_with_provenance(resource, attr, PropagationMode.DOWN)
            if prov.value is None:
                issues.append(f"Missing: {attr}")
        
        if issues:
            print(f"\n{resource.path}")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print(f"\n{resource.path} ✓")
            for attr in required_attrs:
                prov = get_value_with_provenance(resource, attr, PropagationMode.DOWN)
                source = "(local)" if prov.source_path == resource.path else f"(from {prov.source_path})"
                print(f"  {attr}: {prov.value} {source}")

validation_report(tree, ["env", "port", "replicas"])
```

## Kubernetes-Style Namespace Configuration

Model Kubernetes namespaces with inherited resource quotas and limits:

```python
from hrcp import ResourceTree, PropagationMode, get_effective_value, get_value_with_provenance

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
        "quota": get_effective_value(ns, "resource_quota", PropagationMode.MERGE_DOWN),
        "limits": get_effective_value(ns, "limit_range", PropagationMode.MERGE_DOWN),
        "network": get_effective_value(ns, "network_policy", PropagationMode.DOWN),
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

## GitOps Repository Configuration

Model a GitOps repository structure with environment promotion:

```python
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
        "replicas": get_effective_value(resource, "replicas", PropagationMode.DOWN),
        "image_policy": get_effective_value(resource, "image_policy", PropagationMode.DOWN),
        "resources": get_effective_value(resource, "resources", PropagationMode.MERGE_DOWN),
    }

# Generate manifests
for env in ["dev", "staging", "prod"]:
    manifest = generate_manifest(tree, "backend", env)
    print(f"{env}: replicas={manifest['replicas']}, cpu_limit={manifest['resources']['limits']['cpu']}")

# dev: replicas=1, cpu_limit=500m
# staging: replicas=3, cpu_limit=500m  
# prod: replicas=5, cpu_limit=2
```

## Multi-Cloud Infrastructure

Manage configuration across multiple cloud providers:

```python
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
        "provider": get_effective_value(resource, "provider", PropagationMode.DOWN),
        "region": get_effective_value(resource, "default_region", PropagationMode.DOWN),
        "tags": get_effective_value(resource, "tags", PropagationMode.MERGE_DOWN),
        "monitoring": get_effective_value(resource, "monitoring", PropagationMode.MERGE_DOWN),
        "backup": get_effective_value(resource, "backup", PropagationMode.MERGE_DOWN),
    }

# Compare AWS vs GCP prod API configs
aws_config = get_infra_config(tree, "/infrastructure/aws/prod/api")
gcp_config = get_infra_config(tree, "/infrastructure/gcp/prod/api")

print("AWS API Tags:", aws_config["tags"])
# {'managed_by': 'terraform', 'team': 'platform', 'cloud': 'aws', 'environment': 'production'}

print("GCP API Tags:", gcp_config["tags"])
# {'managed_by': 'terraform', 'team': 'platform', 'cloud': 'gcp', 'environment': 'production'}
```

## Game Server Configuration

Configure game servers with region-specific settings:

```python
tree = ResourceTree(root_name="game")

# Global game settings
tree.root.set_attribute("version", "2.1.0")
tree.root.set_attribute("tick_rate", 64)
tree.root.set_attribute("max_players", 100)
tree.root.set_attribute("anti_cheat", {"enabled": True, "level": "standard"})
tree.root.set_attribute("matchmaking", {
    "skill_range": 500,
    "wait_time_max": 120,
    "backfill": True
})

# Regional configurations
regions = {
    "na-east": {"latency_target": 30, "datacenter": "nyc"},
    "na-west": {"latency_target": 35, "datacenter": "lax"},
    "eu-west": {"latency_target": 25, "datacenter": "ams"},
    "asia": {"latency_target": 40, "datacenter": "sgp"},
}

for region, attrs in regions.items():
    tree.create(f"/game/{region}", attributes=attrs)
    # Each region has multiple server pools
    tree.create(f"/game/{region}/ranked", attributes={
        "mode": "ranked",
        "anti_cheat": {"level": "strict"},
        "matchmaking": {"skill_range": 200}
    })
    tree.create(f"/game/{region}/casual", attributes={
        "mode": "casual",
        "matchmaking": {"skill_range": 1000, "backfill": True}
    })

# Tournament servers with special config
tree.create("/game/tournament", attributes={
    "tick_rate": 128,
    "max_players": 10,
    "anti_cheat": {"enabled": True, "level": "maximum"},
    "matchmaking": {"skill_range": 0, "wait_time_max": 300}
})

def get_server_config(tree, server_path):
    """Get full server configuration."""
    server = tree.get(server_path)
    return {
        "version": get_effective_value(server, "version", PropagationMode.DOWN),
        "tick_rate": get_effective_value(server, "tick_rate", PropagationMode.DOWN),
        "max_players": get_effective_value(server, "max_players", PropagationMode.DOWN),
        "latency_target": get_effective_value(server, "latency_target", PropagationMode.DOWN),
        "anti_cheat": get_effective_value(server, "anti_cheat", PropagationMode.MERGE_DOWN),
        "matchmaking": get_effective_value(server, "matchmaking", PropagationMode.MERGE_DOWN),
    }

# Compare ranked vs casual in NA-East
ranked = get_server_config(tree, "/game/na-east/ranked")
casual = get_server_config(tree, "/game/na-east/casual")

print("NA-East Ranked:")
print(f"  Skill range: {ranked['matchmaking']['skill_range']}")  # 200
print(f"  Anti-cheat: {ranked['anti_cheat']['level']}")          # strict

print("\nNA-East Casual:")
print(f"  Skill range: {casual['matchmaking']['skill_range']}")  # 1000
print(f"  Anti-cheat: {casual['anti_cheat']['level']}")          # standard

# Tournament config
tournament = get_server_config(tree, "/game/tournament")
print(f"\nTournament tick rate: {tournament['tick_rate']}")      # 128
```

## E-commerce Product Catalog

Manage product categories with inherited attributes:

```python
tree = ResourceTree(root_name="catalog")

# Store-wide defaults
tree.root.set_attribute("currency", "USD")
tree.root.set_attribute("tax_rate", 0.08)
tree.root.set_attribute("shipping", {"free_threshold": 50, "flat_rate": 5.99})
tree.root.set_attribute("return_policy", {"days": 30, "restocking_fee": 0})

# Electronics category
tree.create("/catalog/electronics", attributes={
    "warranty": {"months": 12},
    "return_policy": {"days": 15, "restocking_fee": 0.15}
})

tree.create("/catalog/electronics/computers", attributes={
    "warranty": {"months": 24}
})
tree.create("/catalog/electronics/computers/laptops", attributes={
    "shipping": {"free_threshold": 0}  # Free shipping on laptops
})

tree.create("/catalog/electronics/phones", attributes={
    "warranty": {"months": 12, "accidental_damage": False}
})

# Clothing category  
tree.create("/catalog/clothing", attributes={
    "return_policy": {"days": 60}  # Extended returns
})
tree.create("/catalog/clothing/shoes")
tree.create("/catalog/clothing/outerwear")

def get_product_policies(tree, category_path):
    """Get all policies applicable to a product category."""
    category = tree.get(category_path)
    return {
        "currency": get_effective_value(category, "currency", PropagationMode.DOWN),
        "tax_rate": get_effective_value(category, "tax_rate", PropagationMode.DOWN),
        "shipping": get_effective_value(category, "shipping", PropagationMode.MERGE_DOWN),
        "warranty": get_effective_value(category, "warranty", PropagationMode.MERGE_DOWN),
        "return_policy": get_effective_value(category, "return_policy", PropagationMode.MERGE_DOWN),
    }

# Compare policies
laptop_policy = get_product_policies(tree, "/catalog/electronics/computers/laptops")
shoes_policy = get_product_policies(tree, "/catalog/clothing/shoes")

print("Laptop policies:")
print(f"  Free shipping: ${laptop_policy['shipping']['free_threshold']}")  # 0 (free)
print(f"  Warranty: {laptop_policy['warranty']['months']} months")         # 24
print(f"  Returns: {laptop_policy['return_policy']['days']} days")         # 15

print("\nShoes policies:")
print(f"  Free shipping: ${shoes_policy['shipping']['free_threshold']}")   # 50
print(f"  Warranty: {shoes_policy['warranty']}")                           # None
print(f"  Returns: {shoes_policy['return_policy']['days']} days")          # 60
```

These examples demonstrate HRCP's flexibility for real-world hierarchical configuration challenges. The combination of inheritance, aggregation, and provenance tracking makes it easy to build maintainable configuration systems.
