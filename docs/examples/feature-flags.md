# Feature Flags

Implement feature flags with hierarchical rollout.

```python
from hrcp import ResourceTree, PropagationMode, get_value

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
        "new_checkout": get_value(user, "new_checkout", PropagationMode.DOWN),
        "dark_mode": get_value(user, "dark_mode", PropagationMode.DOWN),
        "ai_suggestions": get_value(user, "ai_suggestions", PropagationMode.DOWN),
    }

print(get_user_features(tree, "/features/beta/user-123"))
# {"new_checkout": True, "dark_mode": True, "ai_suggestions": True}

print(get_user_features(tree, "/features/beta/user-456"))
# {"new_checkout": True, "dark_mode": True, "ai_suggestions": False}

print(get_user_features(tree, "/features/canary/user-789"))
# {"new_checkout": True, "dark_mode": False, "ai_suggestions": False}
```

## Key Patterns

- **Global defaults** (all features off) at root
- **Cohort-based rollout** (beta, canary groups)
- **Individual overrides** for opt-in/opt-out
- **Fallback to root** for unknown users
