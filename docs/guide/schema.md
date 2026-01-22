# Schema Validation

HRCP lets you define schemas for attributes, ensuring values meet your requirements before they're set.

## Defining Schemas

Use `tree.define()` to specify constraints for an attribute:

```python
from hrcp import ResourceTree

tree = ResourceTree(root_name="platform")

# Define a port attribute: must be an integer between 1 and 65535
tree.define("port", type_=int, ge=1, le=65535)

# Define an environment attribute: must be one of these choices
tree.define("env", choices=("dev", "staging", "prod"))

# Define a timeout: must be a positive number
tree.define("timeout", type_=(int, float), gt=0)
```

## Schema Constraints

| Constraint | Description | Example |
|------------|-------------|---------|
| `type_` | Required type(s) | `type_=int`, `type_=(int, float)` |
| `choices` | Allowed values | `choices=("a", "b", "c")` |
| `ge` | Greater than or equal | `ge=0` |
| `gt` | Greater than | `gt=0` |
| `le` | Less than or equal | `le=100` |
| `lt` | Less than | `lt=100` |
| `min_length` | Minimum string/list length | `min_length=1` |
| `max_length` | Maximum string/list length | `max_length=255` |
| `pattern` | Regex pattern for strings | `pattern=r"^[a-z]+$"` |

## Validation in Action

Once a schema is defined, invalid values are rejected:

```python
tree.define("port", type_=int, ge=1, le=65535)

# Valid
tree.root.set_attribute("port", 8080)  # OK

# Invalid type
tree.root.set_attribute("port", "8080")  # ValidationError: expected int

# Invalid range
tree.root.set_attribute("port", 0)       # ValidationError: must be >= 1
tree.root.set_attribute("port", 70000)   # ValidationError: must be <= 65535
```

## Common Schema Patterns

### Enumerated Values

```python
# Status must be one of these values
tree.define("status", choices=("active", "inactive", "pending"))

tree.root.set_attribute("status", "active")    # OK
tree.root.set_attribute("status", "unknown")   # ValidationError
```

### Numeric Ranges

```python
# Replicas: 1 to 100
tree.define("replicas", type_=int, ge=1, le=100)

# Percentage: 0.0 to 1.0
tree.define("threshold", type_=float, ge=0.0, le=1.0)

# Positive integers only
tree.define("count", type_=int, gt=0)
```

### String Constraints

```python
# Non-empty string
tree.define("name", type_=str, min_length=1)

# Limited length
tree.define("description", type_=str, max_length=500)

# Pattern matching
tree.define("slug", type_=str, pattern=r"^[a-z0-9-]+$")

# Email-like pattern
tree.define("email", type_=str, pattern=r"^[\w.-]+@[\w.-]+\.\w+$")
```

### Multiple Types

```python
# Accept int or float for timeout
tree.define("timeout", type_=(int, float), gt=0)

tree.root.set_attribute("timeout", 30)      # OK (int)
tree.root.set_attribute("timeout", 30.5)    # OK (float)
tree.root.set_attribute("timeout", "30")    # ValidationError
```

## Optional vs Required

By default, attributes can be absent (None). Schemas validate only when values are set:

```python
tree.define("port", type_=int, ge=1, le=65535)

# Not setting the attribute is fine
resource = tree.get("/platform/api")
port = resource.get_attribute("port")  # None - OK

# But if you set it, it must be valid
resource.set_attribute("port", 8080)   # OK
resource.set_attribute("port", -1)     # ValidationError
```

To require an attribute, validate at application level:

```python
def validate_required(resource, required_attrs):
    """Ensure required attributes are set."""
    missing = []
    for attr in required_attrs:
        if resource.get_attribute(attr) is None:
            missing.append(attr)
    if missing:
        raise ValueError(f"Missing required attributes: {missing}")
```

## Schema Inheritance

Schemas are defined at the tree level and apply to all resources:

```python
tree = ResourceTree(root_name="platform")
tree.define("port", type_=int, ge=1, le=65535)

# Schema applies everywhere in the tree
tree.root.set_attribute("port", 8080)  # Validated
tree.create("/platform/api", attributes={"port": 3000})  # Validated
tree.get("/platform/api").set_attribute("port", 9000)  # Validated
```

## Validation Errors

When validation fails, a `ValidationError` is raised with details:

```python
from hrcp import ValidationError

tree.define("port", type_=int, ge=1, le=65535)

try:
    tree.root.set_attribute("port", "not a number")
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Validation failed: port: expected int, got str
```

## Required Fields

Mark attributes as required to ensure they're set on all resources:

```python
tree = ResourceTree(root_name="services")

# Define required attributes
tree.define("name", type_=str, required=True, description="Service name")
tree.define("owner", type_=str, required=True, description="Team that owns this service")
tree.define("port", type_=int, ge=1, le=65535)

# Create services
tree.create("/services/api", attributes={
    "name": "API Gateway",
    "owner": "platform-team",
    "port": 8080
})
tree.create("/services/db", attributes={
    "name": "Database",
    # Missing owner!
    "port": 5432
})
tree.create("/services/cache")  # Missing both name and owner!
```

### Check Missing Required Fields

```python
# Check a single resource
api = tree.get("/services/api")
missing = tree.get_missing_required(api)
print(missing)  # [] - all required fields present

db = tree.get("/services/db")
missing = tree.get_missing_required(db)
print(missing)  # ['owner']

cache = tree.get("/services/cache")
missing = tree.get_missing_required(cache)
print(missing)  # ['name', 'owner']
```

### Validate Required Fields

```python
# Validate and raise if missing
try:
    tree.validate_required(cache)
except ValueError as e:
    print(e)  # "Missing required attributes: ['name', 'owner']"
```

## Tree-Wide Validation

### Validate All Resources

```python
# Check entire tree for validation errors
errors = tree.validate_all()
print(errors)
# {
#     '/services': ['name', 'owner'],       # Root missing required
#     '/services/db': ['owner'],             # DB missing owner
#     '/services/cache': ['name', 'owner']   # Cache missing both
# }
```

### Check if Tree is Valid

```python
# Quick boolean check
if tree.is_valid():
    print("All validations passed!")
else:
    print("Tree has validation errors")
```

### Generate Validation Summary

```python
# Human-readable validation report
summary = tree.validation_summary()
print(summary)
# Validation Summary
# =================
# 
# /services
#   Missing: name (Service name)
#   Missing: owner (Team that owns this service)
# 
# /services/db
#   Missing: owner (Team that owns this service)
# 
# /services/cache
#   Missing: name (Service name)
#   Missing: owner (Team that owns this service)
# 
# Total: 3 resources with errors
```

### Validate Subtree Only

```python
# Validate only a specific subtree
errors = tree.validate_all(path="/services/api")
print(errors)  # {} - api subtree is valid
```

## Schema with Defaults

Get a default value when an attribute isn't set:

```python
tree = ResourceTree(root_name="config")
tree.define("timeout", type_=int, default=30)
tree.define("retries", type_=int, default=3)
tree.define("debug", type_=bool, default=False)

tree.create("/config/api", attributes={"timeout": 60})

api = tree.get("/config/api")

# Get with default fallback
timeout = tree.get_attribute_or_default(api, "timeout")  # 60 (set locally)
retries = tree.get_attribute_or_default(api, "retries")  # 3 (default)
debug = tree.get_attribute_or_default(api, "debug")      # False (default)
```

## JSON Schema Export

Export your schema definitions as JSON Schema for documentation or integration:

```python
tree = ResourceTree(root_name="config")
tree.define("port", type_=int, ge=1, le=65535, description="Service port")
tree.define("env", choices=("dev", "staging", "prod"), description="Environment")
tree.define("timeout", type_=(int, float), gt=0, description="Request timeout in seconds")

# Export as JSON Schema
json_schema = tree.to_json_schema()
print(json_schema)
# {
#     "type": "object",
#     "properties": {
#         "port": {
#             "type": "integer",
#             "minimum": 1,
#             "maximum": 65535,
#             "description": "Service port"
#         },
#         "env": {
#             "enum": ["dev", "staging", "prod"],
#             "description": "Environment"
#         },
#         "timeout": {
#             "type": "number",
#             "exclusiveMinimum": 0,
#             "description": "Request timeout in seconds"
#         }
#     }
# }
```

## Complete Example

```python
from hrcp import ResourceTree, ValidationError

tree = ResourceTree(root_name="platform")

# Define all schemas upfront
tree.define("env", choices=("dev", "staging", "prod"), required=True)
tree.define("port", type_=int, ge=1, le=65535)
tree.define("replicas", type_=int, ge=1, le=100, default=1)
tree.define("timeout", type_=(int, float), gt=0, default=30)
tree.define("name", type_=str, min_length=1, max_length=100, required=True)
tree.define("owner", type_=str, required=True, description="Owning team")
tree.define("tags", type_=list)
tree.define("config", type_=dict)

# Set validated attributes
tree.root.set_attribute("env", "prod")
tree.root.set_attribute("name", "Platform")
tree.root.set_attribute("owner", "platform-team")

tree.create("/platform/api", attributes={
    "name": "API Service",
    "owner": "api-team",
    "port": 8080,
    "replicas": 3,
    "tags": ["critical", "public"],
    "config": {"debug": False}
})

# Validation prevents bad data
try:
    tree.create("/platform/bad", attributes={
        "name": "Bad Service",
        "owner": "unknown",
        "port": 99999  # Invalid!
    })
except ValidationError as e:
    print(f"Blocked invalid config: {e}")

# Check tree validity
if tree.is_valid():
    print("Configuration is valid!")
else:
    print(tree.validation_summary())
```
