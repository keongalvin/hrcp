# Multi-Tenant SaaS Platform

Manage configuration for a SaaS platform with organizations, tenants, and projects.

```python
from hrcp import ResourceTree, PropagationMode, get_value

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

timeout = get_value(analytics, "timeout", PropagationMode.INHERIT)
# 120 (local override)

rate_limit = get_value(analytics, "max_requests_per_minute", PropagationMode.INHERIT)
# 10000 (from tenant)

features = get_value(analytics, "features", PropagationMode.MERGE)
# {"dark_mode": False, "beta_features": False, "ai_assist": True}
# ai_assist merged from tenant, others from platform
```

## Key Patterns

- **Platform defaults** at root level apply to all tenants
- **Tenant overrides** customize limits and features per customer
- **Project inheritance** means less configuration to manage
- **MERGE** for feature flags allows partial overrides
