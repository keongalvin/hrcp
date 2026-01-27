# Use Cases

Real-world examples of how HRCP solves hierarchical configuration problems.

## By Domain

### Cloud & Infrastructure

<div class="grid cards" markdown>

-   :material-cloud:{ .lg .middle } **[Multi-Cloud Infrastructure](multi-cloud.md)**

    ---

    Manage configuration across AWS, GCP, and other providers with unified tagging and monitoring.

-   :material-server:{ .lg .middle } **[Infrastructure Config](infrastructure-config.md)**

    ---

    Model cloud infrastructure with inherited settings for environments and services.

-   :material-kubernetes:{ .lg .middle } **[Kubernetes Namespaces](kubernetes-namespaces.md)**

    ---

    Resource quotas and limit ranges with environment-based inheritance.

-   :material-git:{ .lg .middle } **[GitOps Config](gitops-config.md)**

    ---

    Environment promotion patterns for GitOps repository structures.

</div>

### Applications & Services

<div class="grid cards" markdown>

-   :material-domain:{ .lg .middle } **[Multi-Tenant SaaS](multi-tenant-saas.md)**

    ---

    Tenant-specific configuration with platform defaults and feature flags.

-   :material-toggle-switch:{ .lg .middle } **[Feature Flags](feature-flags.md)**

    ---

    Hierarchical rollout with beta groups, canary deployments, and user overrides.

-   :material-gamepad-variant:{ .lg .middle } **[Game Servers](game-servers.md)**

    ---

    Regional settings, game modes, and matchmaking configuration.

-   :material-cart:{ .lg .middle } **[E-commerce Catalog](ecommerce-catalog.md)**

    ---

    Product categories with inherited shipping, returns, and warranty policies.

</div>

### Organization & Access

<div class="grid cards" markdown>

-   :material-currency-usd:{ .lg .middle } **[Budget Rollup](budget-rollup.md)**

    ---

    Aggregate budgets from teams to departments to organization using UP propagation.

-   :material-shield-account:{ .lg .middle } **[Access Control](access-control.md)**

    ---

    Role-based permissions with inheritance through organizational hierarchy.

-   :material-file-document-check:{ .lg .middle } **[Configuration Audit](config-audit.md)**

    ---

    Generate audit reports showing where every value comes from.

</div>

## By Propagation Mode

| Mode | Best For | Examples |
|------|----------|----------|
| **DOWN** | Defaults & inheritance | [SaaS](multi-tenant-saas.md), [Feature Flags](feature-flags.md), [Infrastructure](infrastructure-config.md) |
| **UP** | Aggregation & rollups | [Budget Rollup](budget-rollup.md), [Access Control](access-control.md) |
| **MERGE_DOWN** | Layered configurations | [Kubernetes](kubernetes-namespaces.md), [GitOps](gitops-config.md), [Multi-Cloud](multi-cloud.md) |
| **NONE** | Local-only values | [Audit](config-audit.md) (checking what's set locally) |

## Common Patterns

### Pattern: Environment Separation

```
/root
  /prod     ← production settings
    /api
    /worker
  /staging  ← staging overrides
    /api
```

See: [Infrastructure Config](infrastructure-config.md), [GitOps Config](gitops-config.md)

### Pattern: Tenant Isolation

```
/platform
  /tenant-a  ← tenant-specific config
    /project-1
  /tenant-b  ← different limits/features
    /project-2
```

See: [Multi-Tenant SaaS](multi-tenant-saas.md)

### Pattern: Regional Variation

```
/service
  /us-east  ← region-specific settings
  /eu-west
  /asia
```

See: [Game Servers](game-servers.md), [Multi-Cloud](multi-cloud.md)

### Pattern: Hierarchical Rollup

```
/org
  /dept-a
    /team-1  ← values aggregate UP
    /team-2
  /dept-b
```

See: [Budget Rollup](budget-rollup.md)
