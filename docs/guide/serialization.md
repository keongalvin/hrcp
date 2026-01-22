# Serialization

HRCP supports multiple formats for saving and loading resource trees: JSON, YAML, and Python dicts.

## JSON

### Save to JSON

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="platform")
tree.root.set_attribute("env", "prod")
tree.create("/platform/api", attributes={"port": 8080})

# Save to file
tree.to_json("config.json")

# Or get as string
json_string = tree.to_json_string()
```

### Load from JSON

```python
# Load from file
tree = ResourceTree.from_json("config.json")

# Or from string
tree = ResourceTree.from_json_string(json_string)
```

### JSON Format

```json
{
  "root_name": "platform",
  "resources": {
    "/platform": {
      "attributes": {
        "env": "prod"
      }
    },
    "/platform/api": {
      "attributes": {
        "port": 8080
      }
    }
  },
  "schemas": {}
}
```

## YAML

YAML is often preferred for human-readable configuration files.

### Save to YAML

```python
# Save to file
tree.to_yaml("config.yaml")

# Or get as string
yaml_string = tree.to_yaml_string()
```

### Load from YAML

```python
# Load from file
tree = ResourceTree.from_yaml_file("config.yaml")

# Or from string
tree = ResourceTree.from_yaml_string(yaml_string)
```

### YAML Format

```yaml
root_name: platform
resources:
  /platform:
    attributes:
      env: prod
  /platform/api:
    attributes:
      port: 8080
schemas: {}
```

## Dictionary

For programmatic manipulation or integration with other systems.

### Convert to Dict

```python
data = tree.to_dict()

# data is a regular Python dict
print(data["root_name"])  # "platform"
print(data["resources"])  # {"/platform": {...}, ...}
```

### Create from Dict

```python
data = {
    "root_name": "platform",
    "resources": {
        "/platform": {
            "attributes": {"env": "prod"}
        },
        "/platform/api": {
            "attributes": {"port": 8080}
        }
    }
}

tree = ResourceTree.from_dict(data)
```

## Schemas in Serialization

Schemas are also serialized and restored:

```python
tree = ResourceTree(root_name="platform")
tree.define("port", type_=int, ge=1, le=65535)
tree.define("env", choices=("dev", "staging", "prod"))

tree.to_yaml("config.yaml")

# Later...
tree = ResourceTree.from_yaml_file("config.yaml")
# Schemas are restored and enforced
```

## Practical Patterns

### Configuration as Code

Store configuration in version control:

```python
# deploy.py
from hrcp import ResourceTree

def load_config():
    """Load configuration from YAML files."""
    tree = ResourceTree.from_yaml_file("config/base.yaml")
    return tree

def main():
    tree = load_config()
    api = tree.get("/platform/api")
    print(f"Deploying to port {api.get_attribute('port')}")

if __name__ == "__main__":
    main()
```

### Environment Layering

Merge base config with environment-specific overrides:

```python
def load_layered_config(env: str) -> ResourceTree:
    """Load base config and apply environment overlay."""
    # Load base
    tree = ResourceTree.from_yaml_file("config/base.yaml")
    
    # Load and merge environment-specific config
    env_file = f"config/{env}.yaml"
    env_tree = ResourceTree.from_yaml_file(env_file)
    
    # Copy environment-specific attributes
    for resource in env_tree.query("/**"):
        target = tree.get(resource.path)
        if target:
            for key, value in resource.attributes.items():
                target.set_attribute(key, value)
    
    return tree

# Usage
tree = load_layered_config("production")
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
import json
from flask import Flask, jsonify, request

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

## Format Comparison

| Feature | JSON | YAML | Dict |
|---------|------|------|------|
| Human readable | Good | Best | N/A |
| Comments | No | Yes | N/A |
| File size | Compact | Larger | N/A |
| Parse speed | Fast | Slower | Instant |
| Programmatic use | Via string | Via string | Direct |

Choose based on your use case:

- **JSON**: APIs, compact storage, JavaScript interop
- **YAML**: Configuration files, human editing
- **Dict**: In-memory manipulation, testing
