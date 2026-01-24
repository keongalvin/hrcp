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
        - delete
        - walk
        - query
        - query_values
        - to_dict
        - from_dict
        - to_json
        - from_json
        - to_yaml
        - from_yaml
        - from_yaml_file
        - to_toml
        - from_toml
        - from_toml_file

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
        - delete_attribute

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
        - key_sources
        - contributing_paths

## Functions

::: hrcp.get_value

## Path Utilities

::: hrcp.normalize_path

::: hrcp.split_path

::: hrcp.join_path

::: hrcp.parent_path

::: hrcp.basename

::: hrcp.match_pattern
