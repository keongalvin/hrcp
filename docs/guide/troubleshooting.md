# Troubleshooting

Common issues and their solutions when working with HRCP.

## Path Errors

### "Path must start with '/{root_name}'"

**Cause**: You're trying to create or access a resource with a path that doesn't match your tree's root name.

```python
tree = ResourceTree(root_name="platform")

# This will fail
try:
    tree.create("/wrong/path")
except ValueError as e:
    print(e)  # Path must start with '/platform'

# This works
tree.create("/platform/path")
```

**Solution**: Ensure all paths start with `/{your_root_name}`.

---

### "Resource already exists at '{path}'"

**Cause**: Attempting to create a resource at a path that already has a resource.

```python
tree = ResourceTree(root_name="org")
tree.create("/org/team")

try:
    tree.create("/org/team")
except ValueError as e:
    print(e)  # Resource already exists at '/org/team'
```

**Solution**: Check if the resource exists before creating, or use `get()` to retrieve the existing one:

```python
existing = tree.get("/org/team")
if existing is None:
    tree.create("/org/team", attributes={"new": True})
else:
    existing.set_attribute("new", True)
```

---

### "name cannot contain '/'"

**Cause**: Resource names cannot contain path separators.

```python
try:
    Resource(name="my/resource")
except ValueError as e:
    print(e)  # name cannot contain '/'
```

**Solution**: Use paths for hierarchy, not slashes in names:

```python
# Wrong: trying to embed hierarchy in name
tree.create("/org/my/resource")  # Creates 3 resources: org, my, resource

# Right: use proper path structure
tree.create("/org/my-resource")  # Single child named "my-resource"
```

---

## Propagation Issues

### Value is None but I expected inheritance

**Cause**: Using `PropagationMode.NONE` instead of `PropagationMode.INHERIT`.

```python
tree = ResourceTree(root_name="org")
tree.root.set_attribute("env", "prod")
tree.create("/org/team")

team = tree.get("/org/team")

# Returns None - NONE only checks local attributes
value = get_value(team, "env", PropagationMode.NONE)

# Returns "prod" - DOWN inherits from ancestors
value = get_value(team, "env", PropagationMode.INHERIT)
```

**Solution**: Use `PropagationMode.INHERIT` for inheritance.

---

### MERGE_DOWN not merging as expected

**Cause**: MERGE_DOWN only merges dictionaries. Non-dict values are replaced entirely.

```python
tree = ResourceTree(root_name="org")
tree.root.set_attribute("tags", ["a", "b"])
tree.create("/org/team", attributes={"tags": ["c"]})

team = tree.get("/org/team")
tags = get_value(team, "tags", PropagationMode.MERGE)
# tags == ["c"], NOT ["a", "b", "c"]
```

**Solution**: For list merging, use `PropagationMode.AGGREGATE` to collect values, then flatten:

```python
# Collect all tags from ancestors manually
def get_merged_tags(resource):
    tags = []
    current = resource
    while current:
        local_tags = current.get_attribute("tags") or []
        tags.extend(local_tags)
        current = current.parent
    return list(set(tags))  # deduplicate
```

---

### UP returns empty list

**Cause**: No descendants have the attribute, or you're querying a leaf node.

```python
tree = ResourceTree(root_name="org")
tree.create("/org/team")  # No "count" attribute set

counts = get_value(tree.root, "count", PropagationMode.AGGREGATE)
# counts == [] - no values found
```

**Solution**: Verify attributes are set on descendant resources:

```python
# Debug: check what attributes exist in subtree
for resource in tree.walk():
    if resource.get_attribute("count") is not None:
        print(f"{resource.path}: count={resource.get_attribute('count')}")
```

---

## Provenance Issues

### Provenance is None

**Cause**: The attribute wasn't found anywhere in the resolution path.

```python
prov = get_value(resource, "nonexistent", PropagationMode.INHERIT, with_provenance=True)
# prov is None (not a Provenance object)
```

**Solution**: This is expected behavior. Always check if `prov is not None` before accessing `.value` or `.source_path`:

```python
prov = get_value(resource, "key", PropagationMode.INHERIT, with_provenance=True)
if prov is not None:
    print(f"Value: {prov.value} from {prov.source_path}")
else:
    print("Attribute not found")
```

---

### key_sources missing keys in MERGE_DOWN

**Cause**: `key_sources` only tracks top-level keys in the merged dict.

```python
tree = ResourceTree(root_name="org")
tree.root.set_attribute("config", {"db": {"host": "localhost", "port": 5432}})
prod = tree.create("/org/prod", attributes={"config": {"db": {"host": "prod.db"}}})

prov = get_value(prod, "config", PropagationMode.MERGE, with_provenance=True)
# prov.key_sources tracks "db.host" and "db.port" with dot notation
print(prov.key_sources)  # {'db.host': '/org/prod', 'db.port': '/org'}
```

**Solution**: For nested key tracking, check `key_sources` which uses dot notation for nested keys (e.g., `"db.host"`).

---

## Serialization Issues

### TypeError when loading from dict

**Cause**: The dict structure doesn't match the expected schema.

```python
data = {"name": "root"}  # Missing 'attributes' and 'children'

try:
    tree = ResourceTree.from_dict(data)
except TypeError as e:
    print(e)  # Missing required keys
```

**Solution**: Ensure all required fields are present:

```python
data = {
    "name": "root",
    "attributes": {},  # Required, can be empty
    "children": {}     # Required, can be empty
}
```

---

### JSON file not loading

**Cause**: File path issues or invalid JSON.

```python
try:
    tree = ResourceTree.from_json("nonexistent.json")
except FileNotFoundError as e:
    print("File not found")
```

**Solution**:
1. Check the file path is correct
2. Validate JSON syntax with `python -m json.tool config.json`
3. Ensure the JSON structure matches the expected schema

---

## Wildcard Issues

### `**` matching too many resources

**Cause**: `**` matches any depth, including the starting resource.

```python
tree.query("/org/**")
# Matches /org, /org/team, /org/team/project, etc.
```

**Solution**: Be more specific with your pattern:

```python
# Match only immediate children
tree.query("/org/*")

# Match at specific depth
tree.query("/org/*/*")

# Match specific suffix
tree.query("/org/**/api")
```

---

### Query returns empty list

**Cause**: Pattern doesn't match any existing paths.

```python
results = tree.query("/org/*/api")
# [] if no resources exist at that pattern
```

**Solution**: Debug by listing all paths:

```python
for resource in tree.walk():
    print(resource.path)
```

---

## Performance Issues

### Slow queries on large trees

**Cause**: `**` wildcards scan the entire subtree.

**Solution**:
1. Use specific patterns: `/org/*/api` instead of `/org/**/api`
2. Limit query scope: `tree.query("/org/team/**")` instead of `tree.query("/org/**")`
3. Cache results if querying repeatedly

---

### Memory usage growing

**Cause**: Large attribute values or deep trees.

**Solution**:
1. Store references/IDs instead of large objects in attributes
2. Consider splitting into multiple trees by domain
3. Use lazy loading patterns for external data

---

## Debugging Tips

### Print tree structure

```python
def print_tree(tree, indent=0):
    """Print the entire tree structure."""
    for resource in tree.walk():
        depth = resource.path.count('/') - 1
        print("  " * depth + f"/{resource.name}: {dict(resource.attributes)}")

print_tree(tree)
```

### Trace value resolution

```python
def trace_value(resource, key, mode):
    """Show where a value comes from."""
    prov = get_value(resource, key, mode, with_provenance=True)
    if prov is None:
        print(f"Query: {resource.path}.{key} - not found")
        return

    print(f"Query: {resource.path}.{key} with {mode.name}")
    print(f"Value: {prov.value}")
    print(f"Source: {prov.source_path}")

    if prov.contributing_paths:
        print(f"Contributors: {prov.contributing_paths}")
    if prov.key_sources:
        print(f"Key sources: {prov.key_sources}")

# Example usage
tree = ResourceTree(root_name="org")
tree.root.set_attribute("config", {"timeout": 30})
my_resource = tree.create("/org/team")
trace_value(my_resource, "config", PropagationMode.MERGE)
```

### Validate tree integrity

```python
def validate_tree(tree):
    """Check for common issues."""
    issues = []

    for resource in tree.walk():
        # Check parent-child consistency
        if resource.parent:
            if resource.name not in resource.parent.children:
                issues.append(f"{resource.path}: not in parent's children")

        # Check for empty names
        if not resource.name:
            issues.append(f"Empty name found at {resource.path}")

    return issues

# Example usage
tree = ResourceTree(root_name="org")
tree.create("/org/team")
issues = validate_tree(tree)
if issues:
    print("Issues found:", issues)
else:
    print("No issues found")
```
