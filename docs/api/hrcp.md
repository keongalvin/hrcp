# hrcp

Main module exporting the public API.

## Usage

```python
from hrcp import ResourceTree, PropagationMode, get_value, Provenance
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
