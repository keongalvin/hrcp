# Serialization

HRCP supports saving and loading resource trees via JSON and Python dicts.

## JSON

### Save to JSON

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="platform")
tree.root.set_attribute("env", "prod")
tree.create("/platform/api", attributes={"port": 8080})

# Save to file
tree.to_json("config.json")
```

### Load from JSON

```python
# Load from file
tree = ResourceTree.from_json("config.json")
```

## Dictionary

For programmatic manipulation or integration with other systems.

### Convert to Dict

```python
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
