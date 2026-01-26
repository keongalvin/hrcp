"""Tests for hrcp version."""

import re

import hrcp


def test_version_exists():
    """hrcp.__version__ should be accessible."""
    assert hasattr(hrcp, "__version__")


def test_version_is_string():
    """__version__ should be a string."""
    assert isinstance(hrcp.__version__, str)


def test_version_is_valid_format():
    """__version__ should be a valid PEP 440 version string."""
    # Matches versions like: 0.1.0, 1.2.3, 0.2.1.dev18, 1.0.0rc1
    pattern = r"^\d+\.\d+\.\d+((a|b|rc)\d+)?(\.dev\d+)?$"
    assert re.match(pattern, hrcp.__version__), (
        f"Invalid version format: {hrcp.__version__}"
    )


def test_version_in_all():
    """__version__ should be exported in __all__."""
    assert "__version__" in hrcp.__all__
