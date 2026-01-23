# hrcp

Main module exporting the public API.

## Usage

```python
from hrcp import (
    ResourceTree,
    Resource,
    PropagationMode,
    get_value,
    Provenance,
    ValidationError,
)
```

## Classes

::: hrcp.ResourceTree
    options:
      members:
        - __init__
        - root
        - create
        - get
        - query
        - query_values
        - define
        - to_json
        - to_json_string
        - from_json
        - from_json_string
        - to_yaml
        - to_yaml_string
        - from_yaml_file
        - from_yaml_string
        - to_dict
        - from_dict

::: hrcp.Resource
    options:
      members:
        - name
        - path
        - parent
        - children
        - attributes
        - set_attribute
        - get_attribute

::: hrcp.PropagationMode
    options:
      members:
        - DOWN
        - UP
        - MERGE_DOWN
        - NONE

::: hrcp.Provenance
    options:
      members:
        - value
        - source_path
        - mode

## Functions

::: hrcp.get_value

## Exceptions

::: hrcp.ValidationError
