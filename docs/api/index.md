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
tree.create("/platform/api")
tree.create("/platform/api", attributes={"port": 8080})
```

### Getting Resources

```python
resource = tree.get("/platform/api")
resources = tree.query("/platform/*")
```

### Setting Attributes

```python
resource.set_attribute("key", "value")
```

### Getting Values

```python
from hrcp import PropagationMode, get_value

# Just the value
value = get_value(resource, "key", PropagationMode.DOWN)

# With provenance tracking
prov = get_value(resource, "key", PropagationMode.DOWN, with_provenance=True)
print(prov.value, prov.source_path)
```

### Serialization

```python
# JSON
tree.to_json("config.json")
tree = ResourceTree.from_json("config.json")

# Dict
data = tree.to_dict()
tree = ResourceTree.from_dict(data)
```

## Full API Documentation

See [hrcp](hrcp.md) for complete API documentation.
