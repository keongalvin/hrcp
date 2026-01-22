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

## Optional Dependencies

HRCP has minimal dependencies:

- **pyyaml**: For YAML serialization support
- **tomli-w**: For TOML serialization support

These are included by default. For a truly dependency-free installation, you can use only JSON serialization.

## Next Steps

Now that you have HRCP installed, head to the [Quick Start](quickstart.md) guide to build your first resource tree.
