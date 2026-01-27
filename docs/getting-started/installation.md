# Installation

## Requirements

HRCP requires Python 3.11 or later.

## Install from PyPI

The recommended way to install HRCP is via pip:

```bash
pip install hrcp
```

## Install with uv

If you're using [uv](https://docs.astral.sh/uv/), the fast Python package manager:

```bash
uv add hrcp
```

## Install from Source

To install the latest development version:

```bash
pip install git+https://github.com/keongalvin/hrcp.git
```

Or clone and install locally:

```bash
git clone https://github.com/keongalvin/hrcp.git
cd hrcp
pip install -e .
```

## Verify Installation

```python
import hrcp
print(hrcp.__version__)
```

## Zero Dependencies

HRCP has **no runtime dependencies**. It uses only Python's standard library:

- `json` for serialization
- `re` for wildcard pattern matching
- `collections.abc` for type hints

This makes HRCP lightweight, fast to install, and free from dependency conflicts.

## Serialization Formats

HRCP provides built-in support for:

| Format | Methods | Notes |
|--------|---------|-------|
| **JSON** | `to_json()`, `from_json()` | Built-in, no dependencies |
| **Dict** | `to_dict()`, `from_dict()` | For programmatic use |

### Using Other Formats

Since `to_dict()` returns a standard Python dict, you can easily serialize to any format:

```python
# YAML (requires pyyaml)
import yaml
data = tree.to_dict()
with open("config.yaml", "w") as f:
    yaml.dump(data, f)

# TOML (requires tomli-w for writing, tomllib for reading in 3.11+)
import tomllib
import tomli_w
data = tree.to_dict()
with open("config.toml", "wb") as f:
    tomli_w.dump(data, f)
```

## Next Steps

Now that you have HRCP installed, head to the [Quick Start](quickstart.md) guide to build your first resource tree.
