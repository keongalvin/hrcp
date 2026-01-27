"""Test that all Python code blocks in documentation are valid and runnable.

Extracts code blocks from markdown files and executes them with HRCP globals
pre-injected. This ensures documentation examples stay in sync with the API.
"""

import pathlib
import re

import pytest

from hrcp import PropagationMode
from hrcp import Provenance
from hrcp import Resource
from hrcp import ResourceTree
from hrcp import get_value

# Collect all markdown files in docs/
DOC_FILES = sorted(pathlib.Path("docs").glob("**/*.md"))

# Common globals to inject into all code blocks
HRCP_GLOBALS = {
    "ResourceTree": ResourceTree,
    "Resource": Resource,
    "PropagationMode": PropagationMode,
    "Provenance": Provenance,
    "get_value": get_value,
}


def extract_python_blocks(text: str) -> list[str]:
    """Extract Python code blocks from markdown text.

    Handles both regular code blocks and indented blocks (e.g., in admonitions).
    Skips blocks that import external dependencies.
    """
    import textwrap

    pattern = r"```python\n(.*?)```"
    blocks = re.findall(pattern, text, re.DOTALL)

    result = []
    for block in blocks:
        dedented = textwrap.dedent(block)

        # Skip blocks with external imports
        has_external = any(
            f"import {ext}" in dedented or f"from {ext}" in dedented
            for ext in EXTERNAL_IMPORTS
        )
        if not has_external:
            result.append(dedented)

    return result


def run_code_blocks(fpath: pathlib.Path, memory: bool = True) -> None:
    """Run all Python code blocks in a markdown file.

    Args:
        fpath: Path to markdown file.
        memory: If True, share state between code blocks (sequential execution).
    """
    text = fpath.read_text()
    blocks = extract_python_blocks(text)

    if not blocks:
        return  # No Python blocks to test

    if memory:
        # Sequential: run all blocks in shared namespace
        # Use __name__ != "__main__" to skip if __name__ == "__main__" guards
        namespace = {"__name__": "__doc_test__", **HRCP_GLOBALS}
        all_code = "\n\n".join(blocks)
        exec(all_code, namespace)
    else:
        # Independent: each block gets fresh namespace
        for i, block in enumerate(blocks):
            namespace = {"__name__": "__doc_test__", **HRCP_GLOBALS}
            try:
                exec(block, namespace)
            except Exception as e:
                raise AssertionError(f"Block {i + 1} failed: {e}") from e


# Files to skip entirely (none currently - all docs are testable)
SKIP_FILES: set[str] = set()

# External imports that indicate a block should be skipped
EXTERNAL_IMPORTS = {"flask", "yaml", "tomli", "tomli_w", "pyyaml"}

# Files where each code block should run independently (not sequentially)
# These have multiple independent examples that would conflict
INDEPENDENT_BLOCKS = {
    "docs/api/index.md",
    "docs/guide/concepts.md",
    "docs/guide/philosophy.md",
    "docs/guide/provenance.md",
    "docs/guide/serialization.md",
}


@pytest.mark.parametrize("fpath", DOC_FILES, ids=str)
def test_docs(fpath):
    """Test that all Python code blocks in a markdown file execute without error."""
    fpath_str = str(fpath)

    if fpath_str in SKIP_FILES:
        pytest.skip(f"Skipped: {fpath} contains illustrative examples")

    memory = fpath_str not in INDEPENDENT_BLOCKS
    run_code_blocks(fpath, memory=memory)
