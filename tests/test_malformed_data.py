"""Tests for handling malformed data in HRCP serialization.

These tests ensure the library handles invalid input gracefully with
clear error messages rather than crashing or silently producing
incorrect results.
"""

import json
import tempfile
from pathlib import Path

import pytest

from hrcp.core import ResourceTree


class TestMalformedDictMissingKeys:
    """Test handling of dicts with missing required keys."""

    def test_from_dict_missing_name_raises_key_error(self):
        """from_dict should raise KeyError when 'name' key is missing."""
        data = {"attributes": {}, "children": {}}

        with pytest.raises(KeyError):
            ResourceTree.from_dict(data)

    def test_from_dict_empty_dict_raises_key_error(self):
        """from_dict should raise KeyError for empty dict."""
        data = {}

        with pytest.raises(KeyError):
            ResourceTree.from_dict(data)

    def test_from_dict_child_missing_name_raises_key_error(self):
        """from_dict should raise KeyError when child is missing 'name' key."""
        data = {
            "name": "root",
            "attributes": {},
            "children": {
                "child1": {"attributes": {}, "children": {}},  # missing 'name'
            },
        }

        with pytest.raises(KeyError):
            ResourceTree.from_dict(data)


class TestMalformedDictWrongTypes:
    """Test handling of dicts with wrong value types."""

    def test_from_dict_name_not_string_raises_type_error(self):
        """from_dict should raise TypeError when name is not a string."""
        data = {"name": 123, "attributes": {}, "children": {}}

        with pytest.raises(TypeError):
            ResourceTree.from_dict(data)

    def test_from_dict_name_is_none_raises_type_error(self):
        """from_dict should raise TypeError when name is None."""
        data = {"name": None, "attributes": {}, "children": {}}

        with pytest.raises(TypeError):
            ResourceTree.from_dict(data)

    def test_from_dict_attributes_not_dict_raises_type_error(self):
        """from_dict should raise TypeError when attributes is not a dict."""
        data = {"name": "root", "attributes": "invalid", "children": {}}

        with pytest.raises(TypeError):
            ResourceTree.from_dict(data)

    def test_from_dict_attributes_is_list_raises_type_error(self):
        """from_dict should raise TypeError when attributes is a list."""
        data = {"name": "root", "attributes": ["a", "b"], "children": {}}

        with pytest.raises(TypeError):
            ResourceTree.from_dict(data)

    def test_from_dict_children_not_dict_raises_type_error(self):
        """from_dict should raise TypeError when children is not a dict."""
        data = {"name": "root", "attributes": {}, "children": "invalid"}

        with pytest.raises(TypeError):
            ResourceTree.from_dict(data)

    def test_from_dict_children_is_list_raises_type_error(self):
        """from_dict should raise TypeError when children is a list."""
        data = {"name": "root", "attributes": {}, "children": ["child1", "child2"]}

        with pytest.raises(TypeError):
            ResourceTree.from_dict(data)

    def test_from_dict_child_data_not_dict_raises_type_error(self):
        """from_dict should raise TypeError when child data is not a dict."""
        data = {
            "name": "root",
            "attributes": {},
            "children": {
                "child1": "not a dict",
            },
        }

        with pytest.raises(TypeError):
            ResourceTree.from_dict(data)


class TestMalformedDictInvalidNames:
    """Test handling of invalid name values."""

    def test_from_dict_empty_name_raises_value_error(self):
        """from_dict should raise ValueError for empty name."""
        data = {"name": "", "attributes": {}, "children": {}}

        with pytest.raises(ValueError, match="name cannot be empty"):
            ResourceTree.from_dict(data)

    def test_from_dict_name_with_slash_raises_value_error(self):
        """from_dict should raise ValueError for name containing '/'."""
        data = {"name": "root/child", "attributes": {}, "children": {}}

        with pytest.raises(ValueError, match="name cannot contain"):
            ResourceTree.from_dict(data)

    def test_from_dict_child_empty_name_raises_value_error(self):
        """from_dict should raise ValueError for child with empty name."""
        data = {
            "name": "root",
            "attributes": {},
            "children": {
                "child1": {"name": "", "attributes": {}, "children": {}},
            },
        }

        with pytest.raises(ValueError, match="name cannot be empty"):
            ResourceTree.from_dict(data)

    def test_from_dict_child_name_with_slash_raises_value_error(self):
        """from_dict should raise ValueError for child name containing '/'."""
        data = {
            "name": "root",
            "attributes": {},
            "children": {
                "child1": {"name": "bad/name", "attributes": {}, "children": {}},
            },
        }

        with pytest.raises(ValueError, match="name cannot contain"):
            ResourceTree.from_dict(data)


class TestMalformedDictInconsistentData:
    """Test handling of inconsistent data structures."""

    def test_from_dict_child_key_mismatch_uses_name_field(self):
        """When child dict key differs from name field, name field is used."""
        data = {
            "name": "root",
            "attributes": {},
            "children": {
                "key_name": {"name": "actual_name", "attributes": {}, "children": {}},
            },
        }

        tree = ResourceTree.from_dict(data)

        # The child should be accessible by its actual name, not the key
        assert tree.get("/root/actual_name") is not None
        assert tree.get("/root/key_name") is None


class TestMalformedJson:
    """Test handling of malformed JSON files."""

    def test_from_json_invalid_json_raises_decode_error(self):
        """from_json should raise JSONDecodeError for invalid JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("{not valid json}")
            path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                ResourceTree.from_json(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_from_json_truncated_json_raises_decode_error(self):
        """from_json should raise JSONDecodeError for truncated JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write('{"name": "root", "attributes": {')
            path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                ResourceTree.from_json(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_from_json_empty_file_raises_decode_error(self):
        """from_json should raise JSONDecodeError for empty file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("")
            path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                ResourceTree.from_json(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_from_json_nonexistent_file_raises_file_not_found(self):
        """from_json should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            ResourceTree.from_json("/nonexistent/path/to/file.json")

    def test_from_json_json_array_raises_type_error(self):
        """from_json should raise TypeError when JSON is an array not object."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(["item1", "item2"], f)
            path = f.name

        try:
            with pytest.raises((TypeError, KeyError)):
                ResourceTree.from_json(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_from_json_json_primitive_raises_type_error(self):
        """from_json should raise TypeError when JSON is a primitive."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump("just a string", f)
            path = f.name

        try:
            with pytest.raises((TypeError, AttributeError)):
                ResourceTree.from_json(path)
        finally:
            Path(path).unlink(missing_ok=True)


class TestMalformedNestedData:
    """Test handling of malformed data in deeply nested structures."""

    def test_from_dict_deeply_nested_missing_name(self):
        """from_dict should catch missing name in deeply nested children."""
        data = {
            "name": "root",
            "attributes": {},
            "children": {
                "level1": {
                    "name": "level1",
                    "attributes": {},
                    "children": {
                        "level2": {
                            "name": "level2",
                            "attributes": {},
                            "children": {
                                "level3": {  # Missing 'name'
                                    "attributes": {},
                                    "children": {},
                                },
                            },
                        },
                    },
                },
            },
        }

        with pytest.raises(KeyError):
            ResourceTree.from_dict(data)

    def test_from_dict_deeply_nested_invalid_name(self):
        """from_dict should catch invalid name in deeply nested children."""
        data = {
            "name": "root",
            "attributes": {},
            "children": {
                "level1": {
                    "name": "level1",
                    "attributes": {},
                    "children": {
                        "level2": {
                            "name": "level2",
                            "attributes": {},
                            "children": {
                                "level3": {
                                    "name": "bad/name",  # Invalid name
                                    "attributes": {},
                                    "children": {},
                                },
                            },
                        },
                    },
                },
            },
        }

        with pytest.raises(ValueError, match="name cannot contain"):
            ResourceTree.from_dict(data)
