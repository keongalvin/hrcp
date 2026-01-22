"""Path utilities for HRCP resource paths."""

from __future__ import annotations


def join_path(*segments: str) -> str:
    """Join path segments into a single path.

    Args:
        *segments: Path segments to join.

    Returns:
        A normalized path with segments joined by /.
    """
    parts = []
    for segment in segments:
        # Strip leading/trailing slashes and split
        clean = segment.strip("/")
        if clean:
            parts.extend(clean.split("/"))

    return "/" + "/".join(parts) if parts else "/"


def split_path(path: str) -> list[str]:
    """Split a path into its segments.

    Args:
        path: A resource path like '/org/team/alice'.

    Returns:
        List of path segments (without leading slash).
    """
    clean = path.strip("/")
    if not clean:
        return []
    # Filter out empty segments from double slashes
    return [s for s in clean.split("/") if s]


def parent_path(path: str) -> str:
    """Get the parent path.

    Args:
        path: A resource path like '/org/team/alice'.

    Returns:
        Parent path, or '/' if path is root.
    """
    segments = split_path(path)
    if len(segments) <= 1:
        return "/"
    return "/" + "/".join(segments[:-1])


def basename(path: str) -> str:
    """Get the last segment of a path.

    Args:
        path: A resource path like '/org/team/alice'.

    Returns:
        Last segment of the path.
    """
    segments = split_path(path)
    return segments[-1] if segments else ""


def normalize_path(path: str) -> str:
    """Normalize a path to canonical form.

    - Ensures leading slash
    - Removes trailing slash
    - Removes double slashes

    Args:
        path: A path string.

    Returns:
        Normalized path.
    """
    # Split and rejoin to handle all cases
    segments = split_path(path)
    if not segments:
        return "/"
    return "/" + "/".join(segments)
