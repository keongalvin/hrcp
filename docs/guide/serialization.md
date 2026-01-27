# Serialization

HRCP supports saving and loading resource trees via JSON and Python dicts.

## JSON

### Save to JSON

```python
import tempfile
import os

tree = ResourceTree(root_name="platform")
tree.root.set_attribute("env", "prod")
tree.create("/platform/api", attributes={"port": 8080})

# Save to file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    config_path = f.name
tree.to_json(config_path)

# Load from file
tree = ResourceTree.from_json(config_path)

# Clean up
os.unlink(config_path)
```

## Dictionary

For programmatic manipulation or integration with other systems.

### Convert to Dict

```python
tree = ResourceTree(root_name="platform")
tree.root.set_attribute("env", "prod")
tree.create("/platform/api", attributes={"port": 8080})

data = tree.to_dict()

# data is a regular Python dict
print(data["name"])        # "platform"
print(data["attributes"])  # {"env": "prod"}
print(data["children"])    # {"api": {...}}
```

### Create from Dict

```python
data = {
    "name": "platform",
    "attributes": {"env": "prod"},
    "children": {
        "api": {
            "name": "api",
            "attributes": {"port": 8080},
            "children": {}
        }
    }
}

tree = ResourceTree.from_dict(data)
```

## Dict Schema Reference

The dictionary format used by `to_dict()` and `from_dict()` follows this schema:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Resource name (unique within parent) |
| `attributes` | `dict[str, Any]` | Yes | Key-value configuration pairs |
| `children` | `dict[str, ResourceDict]` | Yes | Child resources keyed by name |

### Schema Definition

```python
from typing import Any, TypedDict

# Type definition for reference
ResourceDict = TypedDict('ResourceDict', {
    'name': str,                          # Required: resource identifier
    'attributes': dict[str, Any],         # Required: configuration data
    'children': dict[str, 'ResourceDict'] # Required: nested resources
})
```

### Validation Rules

- `name` must be a non-empty string without `/` characters
- `attributes` must be a dict (can be empty `{}`)
- `children` must be a dict (can be empty `{}`)
- Child keys must match the child's `name` field
- All values in `attributes` should be JSON-serializable

### Example: Complete Tree

```python
{
    "name": "platform",
    "attributes": {
        "env": "production",
        "timeout": 30
    },
    "children": {
        "us-east": {
            "name": "us-east",
            "attributes": {"region": "us-east-1"},
            "children": {
                "api": {
                    "name": "api",
                    "attributes": {"port": 8080, "replicas": 3},
                    "children": {}
                },
                "db": {
                    "name": "db",
                    "attributes": {"engine": "postgres"},
                    "children": {}
                }
            }
        }
    }
}
```

## Practical Patterns

### Configuration as Code

Store configuration in version control:

```python
from hrcp import ResourceTree

def load_config():
    """Load configuration from JSON."""
    return ResourceTree.from_json("config/base.json")

def main():
    tree = load_config()
    api = tree.get("/platform/api")
    print(f"Deploying to port {api.get_attribute('port')}")

if __name__ == "__main__":
    main()
```

### Backup and Restore

```python
import datetime

def backup_tree(tree: ResourceTree, backup_dir: str) -> str:
    """Create a timestamped backup."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{backup_dir}/config_{timestamp}.json"
    tree.to_json(filename)
    return filename

def restore_tree(backup_file: str) -> ResourceTree:
    """Restore from backup."""
    return ResourceTree.from_json(backup_file)
```

### API Integration

```python
from flask import Flask, jsonify, request
from hrcp import ResourceTree

app = Flask(__name__)
tree = ResourceTree(root_name="config")

@app.route("/config", methods=["GET"])
def get_config():
    """Return tree as JSON."""
    return jsonify(tree.to_dict())

@app.route("/config", methods=["PUT"])
def update_config():
    """Replace tree from JSON."""
    global tree
    data = request.json
    tree = ResourceTree.from_dict(data)
    return jsonify({"status": "ok"})

@app.route("/config/resource/<path:resource_path>", methods=["GET"])
def get_resource(resource_path):
    """Get a specific resource."""
    resource = tree.get(f"/{resource_path}")
    if resource:
        return jsonify({
            "path": resource.path,
            "attributes": dict(resource.attributes)
        })
    return jsonify({"error": "not found"}), 404
```
