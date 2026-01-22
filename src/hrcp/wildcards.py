"""Wildcard pattern matching for HRCP paths.

Supports:
- Single wildcard (*): matches any single path segment
- Double wildcard (**): matches any number of segments (including zero)
"""

from __future__ import annotations

import re


def match_pattern(path: str, pattern: str) -> bool:
    """Check if a path matches a wildcard pattern.

    Args:
        path: The resource path to check (e.g., '/infra/region/server').
        pattern: The pattern to match against (e.g., '/infra/*/server').

    Returns:
        True if the path matches the pattern, False otherwise.

    Examples:
        >>> match_pattern('/infra/us/server', '/infra/*/server')
        True
        >>> match_pattern('/infra/us/dc/server', '/infra/*/server')
        False
        >>> match_pattern('/infra/us/dc/server', '/infra/**/server')
        True
    """
    # Convert pattern to regex
    regex = pattern_to_regex(pattern)
    return bool(re.match(regex, path))


def pattern_to_regex(pattern: str) -> str:
    """Convert a wildcard pattern to a regular expression.

    Args:
        pattern: The wildcard pattern.

    Returns:
        A regex string that matches the pattern.
    """
    # Split pattern into segments
    segments = pattern.strip("/").split("/")

    regex_parts: list[str] = []
    i = 0

    while i < len(segments):
        seg = segments[i]

        if seg == "**":
            # ** matches zero or more path segments
            # Look ahead to see what comes after
            if i + 1 < len(segments):
                # There's more pattern after **
                # Match any path that eventually leads to the remaining pattern
                remaining = "/" + "/".join(segments[i + 1 :])
                remaining_regex = pattern_to_regex(remaining)
                # Remove the start anchor from remaining_regex
                remaining_regex = remaining_regex.lstrip("^")
                regex_parts.append(f"(?:/[^/]+)*{remaining_regex}")
                break  # Rest is handled by remaining_regex
            # ** at the end - match anything remaining
            regex_parts.append("(?:/[^/]+)*")
        elif seg == "*":
            # * matches exactly one path segment
            regex_parts.append("/[^/]+")
        elif "*" in seg:
            # Segment contains wildcard (e.g., "server*")
            escaped = re.escape(seg).replace(r"\*", "[^/]*")
            regex_parts.append(f"/{escaped}")
        else:
            # Literal segment
            regex_parts.append(f"/{re.escape(seg)}")

        i += 1

    return "^" + "".join(regex_parts) + "$"
