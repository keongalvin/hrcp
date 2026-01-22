"""Tests for HRCP path utilities.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

from hypothesis import given
from hypothesis import strategies as st

from hrcp.path import basename
from hrcp.path import join_path
from hrcp.path import normalize_path
from hrcp.path import parent_path
from hrcp.path import split_path

# Strategy for path segments (no slashes, non-empty)
segment = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)


class TestJoinPath:
    """Test path joining."""

    @given(base=segment, child=segment)
    def test_join_simple(self, base, child):
        """join_path combines path segments."""
        result = join_path(f"/{base}", child)
        assert result == f"/{base}/{child}"

    @given(segments=st.lists(segment, min_size=2, max_size=5))
    def test_join_multiple(self, segments):
        """join_path handles multiple segments."""
        result = join_path(f"/{segments[0]}", *segments[1:])
        expected = "/" + "/".join(segments)
        assert result == expected

    @given(base=segment, child=segment)
    def test_join_handles_trailing_slash(self, base, child):
        """join_path handles trailing slashes."""
        result = join_path(f"/{base}/", child)
        assert result == f"/{base}/{child}"

    @given(base=segment, child=segment)
    def test_join_handles_leading_slash_in_segment(self, base, child):
        """join_path handles leading slash in segment."""
        result = join_path(f"/{base}", f"/{child}")
        assert result == f"/{base}/{child}"


class TestSplitPath:
    """Test path splitting."""

    @given(segments=st.lists(segment, min_size=1, max_size=5))
    def test_split_simple(self, segments):
        """split_path returns list of segments."""
        path = "/" + "/".join(segments)
        result = split_path(path)
        assert result == segments

    @given(name=segment)
    def test_split_root(self, name):
        """split_path handles root path."""
        assert split_path(f"/{name}") == [name]

    def test_split_empty(self):
        """split_path handles empty/root."""
        assert split_path("/") == []


class TestParentPath:
    """Test getting parent path."""

    @given(segments=st.lists(segment, min_size=2, max_size=5))
    def test_parent_simple(self, segments):
        """parent_path returns parent directory."""
        path = "/" + "/".join(segments)
        expected = "/" + "/".join(segments[:-1])
        assert parent_path(path) == expected

    @given(parent=segment, child=segment)
    def test_parent_of_child(self, parent, child):
        """parent_path of direct child is parent."""
        assert parent_path(f"/{parent}/{child}") == f"/{parent}"

    @given(name=segment)
    def test_parent_of_root(self, name):
        """parent_path of root-level is root."""
        assert parent_path(f"/{name}") == "/"


class TestBasename:
    """Test getting path basename."""

    @given(segments=st.lists(segment, min_size=1, max_size=5))
    def test_basename_simple(self, segments):
        """basename returns last segment."""
        path = "/" + "/".join(segments)
        assert basename(path) == segments[-1]

    @given(name=segment)
    def test_basename_root(self, name):
        """basename of root path."""
        assert basename(f"/{name}") == name


class TestNormalizePath:
    """Test path normalization."""

    @given(segments=st.lists(segment, min_size=1, max_size=5))
    def test_normalize_adds_leading_slash(self, segments):
        """normalize_path adds leading slash if missing."""
        path = "/".join(segments)
        result = normalize_path(path)
        assert result.startswith("/")
        assert result == "/" + "/".join(segments)

    @given(segments=st.lists(segment, min_size=1, max_size=5))
    def test_normalize_removes_trailing_slash(self, segments):
        """normalize_path removes trailing slash."""
        path = "/" + "/".join(segments) + "/"
        result = normalize_path(path)
        assert not result.endswith("/")

    @given(seg1=segment, seg2=segment)
    def test_normalize_removes_double_slashes(self, seg1, seg2):
        """normalize_path removes double slashes."""
        result = normalize_path(f"/{seg1}//{seg2}")
        assert "//" not in result
        assert result == f"/{seg1}/{seg2}"

    @given(segments=st.lists(segment, min_size=1, max_size=5))
    def test_normalize_already_clean(self, segments):
        """normalize_path handles already clean paths."""
        path = "/" + "/".join(segments)
        assert normalize_path(path) == path
