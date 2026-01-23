# API Reference

This section provides detailed API documentation for all HRCP modules.

## Module Overview

| Module | Description |
|--------|-------------|
| [`hrcp`](hrcp.md) | Main package - exports all public API |
| `hrcp.core` | Core classes: `ResourceTree`, `Resource` |
| `hrcp.propagation` | `PropagationMode` enum and propagation logic |
| `hrcp.provenance` | Provenance tracking |
| `hrcp.schema` | Schema validation |
| `hrcp.wildcards` | Wildcard pattern matching |
| `hrcp.path` | Path utilities |

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

### Defining Schemas

```python
tree.define("port", type_=int, ge=1, le=65535)
tree.define("env", choices=("dev", "staging", "prod"))
```

### Serialization

```python
# JSON
tree.to_json("config.json")
tree = ResourceTree.from_json("config.json")

# YAML
tree.to_yaml("config.yaml")
tree = ResourceTree.from_yaml_file("config.yaml")

# Dict
data = tree.to_dict()
tree = ResourceTree.from_dict(data)
```

## Full API Documentation

See [hrcp](hrcp.md) for complete API documentation with all classes, methods, and parameters.
