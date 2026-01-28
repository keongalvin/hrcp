# hrcp

Main module exporting the public API.

## Usage

```python
from hrcp import ResourceTree, Resource, PropagationMode, get_value, Provenance
```

## Classes

::: hrcp.Resource
    options:
      members:
        - __init__
        - name
        - path
        - parent
        - children
        - attributes
        - add_child
        - remove_child
        - get_child
        - set_attribute
        - get_attribute
        - delete_attribute

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

::: hrcp.PropagationMode
    options:
      members:
        - INHERIT
        - AGGREGATE
        - MERGE
        - REQUIRE_PATH
        - COLLECT_ANCESTORS
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
