# Organization Budget Rollup

Aggregate budgets from teams up to the organization level.

```python
from hrcp import ResourceTree, PropagationMode, get_value

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
    budgets = get_value(resource, "budget", PropagationMode.AGGREGATE)
    return sum(budgets) if budgets else 0

print(f"Engineering total: ${get_total_budget(tree.get('/company/engineering')):,}")
# Engineering total: $1,000,000

print(f"Company total: ${get_total_budget(tree.root):,}")
# Company total: $1,500,000
```

## With Provenance

Track which teams contribute to totals:

```python
def budget_breakdown(resource):
    """Show budget breakdown with sources."""
    prov = get_value(resource, "budget", PropagationMode.AGGREGATE, with_provenance=True)

    print(f"\nBudget breakdown for {resource.path}")
    print("-" * 40)

    total = 0
    for path, budget in zip(prov.contributing_paths, prov.value):
        print(f"  {path}: ${budget:,}")
        total += budget

    print(f"  {'Total':.<30} ${total:,}")

budget_breakdown(tree.get("/company/engineering"))
# Budget breakdown for /company/engineering
# ----------------------------------------
#   /company/engineering: $500,000
#   /company/engineering/platform: $200,000
#   /company/engineering/mobile: $150,000
#   /company/engineering/web: $150,000
#   Total......................... $1,000,000
```

## Key Patterns

- **UP propagation** collects values from all descendants
- **`contributing_paths`** tracks which resources contributed
- **Hierarchical totals** at any level (team, department, company)
