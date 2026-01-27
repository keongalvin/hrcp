# Access Control Inheritance

Implement role-based access control with inherited permissions.

```python
from hrcp import ResourceTree, PropagationMode, get_value

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

# Check if user has admin access via inheritance
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

## Collecting All Admins

Use UP propagation to find all admins with access:

```python
def get_all_admins_with_access(resource):
    """Get all admins from resource up to root."""
    all_admins = set()
    current = resource
    while current:
        admins = current.get_attribute("admins") or []
        all_admins.update(admins)
        current = current.parent
    return list(all_admins)

admins = get_all_admins_with_access(tree.get("/org/engineering/secrets"))
# ["alice@company.com", "bob@company.com"]
```

## Key Patterns

- **Inherited permissions** flow from parent to child
- **Manual traversal** for cumulative permission checks
- **Empty lists** can restrict without removing inheritance
- **Separation of roles** (admins vs viewers)
