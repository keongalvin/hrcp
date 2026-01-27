# API Reference

## Public API

```python
from hrcp import ResourceTree, Resource, PropagationMode, get_value, Provenance
```

Five exports—everything you need for hierarchical configuration with provenance.

## Quick Reference

### Creating Trees

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="platform")
```

### Creating Resources

```python
tree = ResourceTree(root_name="platform")
tree.create("/platform/api")
tree.create("/platform/db", attributes={"port": 5432})
```

### Getting Resources

```python
tree = ResourceTree(root_name="platform")
tree.create("/platform/api")
tree.create("/platform/db")

resource = tree.get("/platform/api")
resources = tree.query("/platform/*")
```

### Setting Attributes

```python
tree = ResourceTree(root_name="platform")
resource = tree.create("/platform/api")
resource.set_attribute("key", "value")
```

### Getting Values

```python
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("key", "default")
resource = tree.create("/platform/api")

# Just the value
value = get_value(resource, "key", PropagationMode.INHERIT)

# With provenance tracking
prov = get_value(resource, "key", PropagationMode.INHERIT, with_provenance=True)
print(prov.value, prov.source_path)
```

### Serialization

```python
tree = ResourceTree(root_name="platform")
tree.create("/platform/api", attributes={"port": 8080})

# Dict
data = tree.to_dict()
tree = ResourceTree.from_dict(data)
```

## Full API Documentation

See [hrcp](hrcp.md) for complete API documentation.
