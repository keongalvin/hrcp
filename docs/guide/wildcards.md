# Wildcards

Wildcards let you query multiple resources at once, making it easy to work with groups of resources that match a pattern.

## Wildcard Patterns

HRCP supports two wildcard characters:

| Pattern | Matches |
|---------|---------|
| `*` | Exactly one path segment |
| `**` | Any number of segments (including zero) |

## Single-Segment Wildcard: `*`

The `*` matches exactly one segment in the path:

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="platform")
tree.create("/platform/us-east/api")
tree.create("/platform/us-west/api")
tree.create("/platform/eu-west/api")
tree.create("/platform/us-east/db")

# Match all regions' api services
results = tree.query("/platform/*/api")
# Returns resources at:
#   /platform/us-east/api
#   /platform/us-west/api
#   /platform/eu-west/api
```

Multiple wildcards can be used:

```python
# Match all services in all regions
results = tree.query("/platform/*/*")
# Returns all services (api, db) in all regions
```

## Multi-Segment Wildcard: `**`

The `**` matches any depth, including zero segments:

```python
tree = ResourceTree(root_name="org")
tree.create("/org/eng/platform/api")
tree.create("/org/eng/platform/db")
tree.create("/org/eng/mobile/ios")
tree.create("/org/sales/crm")

# Match all resources under /org/eng at any depth
results = tree.query("/org/eng/**")
# Returns:
#   /org/eng
#   /org/eng/platform
#   /org/eng/platform/api
#   /org/eng/platform/db
#   /org/eng/mobile
#   /org/eng/mobile/ios

# Match all 'api' resources anywhere in the tree
results = tree.query("/org/**/api")
# Returns:
#   /org/eng/platform/api
```

## Query Methods

### `tree.query(pattern)`

Returns a list of resources matching the pattern:

```python
resources = tree.query("/platform/*/api")

for resource in resources:
    print(f"{resource.path}: {resource.get_attribute('port')}")
```

### `tree.query_values(pattern, attr, mode)`

Query attribute values across matching resources:

```python
from hrcp import PropagationMode

# Get all timeout values for API services
timeouts = tree.query_values("/platform/*/api", "timeout", PropagationMode.NONE)
# Returns a list of values (excludes None values)
# [60, 30, 45]
```

## Practical Examples

### Check Configuration Consistency

Verify all services have the required configuration:

```python
def check_required_config(tree, pattern, required_attrs):
    """Check that all matching resources have required attributes."""
    resources = tree.query(pattern)
    issues = []

    for resource in resources:
        for attr in required_attrs:
            if resource.get_attribute(attr) is None:
                issues.append(f"{resource.path} missing {attr}")

    return issues

issues = check_required_config(
    tree,
    "/platform/**/api",
    ["port", "health_check_path"]
)
```

### Bulk Updates

Apply configuration to multiple resources:

```python
def set_on_matching(tree, pattern, attr, value):
    """Set attribute on all resources matching pattern."""
    resources = tree.query(pattern)
    count = 0

    for resource in resources:
        resource.set_attribute(attr, value)
        count += 1

    return count

# Enable feature flag on all API services
updated = set_on_matching(tree, "/platform/**/api", "feature_x_enabled", True)
print(f"Updated {updated} resources")
```

### Configuration Report

Generate a report across resources:

```python
def config_report(tree, pattern, attrs):
    """Generate config report for matching resources."""
    resources = tree.query(pattern)

    print(f"Configuration Report: {pattern}")
    print("=" * 60)

    for resource in resources:
        print(f"\n{resource.path}")
        for attr in attrs:
            value = resource.get_attribute(attr)
            status = "✓" if value is not None else "✗"
            print(f"  {status} {attr}: {value}")

config_report(tree, "/platform/*/api", ["port", "replicas", "timeout"])
```

### Find Resources by Attribute

Find resources that have a specific attribute value:

```python
def find_by_attribute(tree, pattern, attr, expected_value):
    """Find resources with specific attribute value."""
    resources = tree.query(pattern)
    return [r for r in resources if r.get_attribute(attr) == expected_value]

# Find all production services
prod_services = find_by_attribute(tree, "/platform/**", "env", "production")
```

## Pattern Matching Rules

1. **Patterns must start with `/`** - They're absolute paths from root
2. **`*` never matches empty** - `/a/*/c` won't match `/a/c`
3. **`**` can match empty** - `/a/**/c` matches both `/a/c` and `/a/b/c`
4. **`**` is greedy** - It matches as many segments as possible

## Performance Considerations

- `*` queries are fast (single level scan)
- `**` queries scan the full subtree
- For large trees, prefer specific patterns over broad wildcards
- Cache results if querying the same pattern repeatedly

```python
# Fast: specific path with single wildcard
tree.query("/platform/*/api")

# Slower: scans entire tree
tree.query("/platform/**")

# Balanced: limits depth
tree.query("/platform/*/*")
```
