"""Tests for HRCP validation reporting.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

from hrcp import ResourceTree


class TestValidationReport:
    """Test validation reporting for entire tree."""

    def test_validate_all_returns_empty_when_valid(self):
        """validate_all() returns empty dict when all valid."""
        tree = ResourceTree(root_name="config")
        tree.define("port", type_=int, required=True)
        tree.root.set_attribute("port", 8080)

        errors = tree.validate_all()

        assert errors == {}

    def test_validate_all_returns_missing_required(self):
        """validate_all() returns dict of paths to missing required fields."""
        tree = ResourceTree(root_name="config")
        tree.define("api_key", type_=str, required=True)
        tree.create("/config/service")

        errors = tree.validate_all()

        # Both root and service are missing api_key
        assert "/config" in errors
        assert "api_key" in errors["/config"]
        assert "/config/service" in errors
        assert "api_key" in errors["/config/service"]

    def test_validate_all_checks_nested_resources(self):
        """validate_all() checks all nested resources."""
        tree = ResourceTree(root_name="org")
        tree.define("name", type_=str, required=True)
        tree.create("/org/team", attributes={"name": "backend"})
        tree.create("/org/team/member")  # Missing name

        errors = tree.validate_all()

        # org and member missing name, team has it
        assert "/org" in errors
        assert "/org/team" not in errors
        assert "/org/team/member" in errors

    def test_validate_all_with_path(self):
        """validate_all(path=...) validates only subtree."""
        tree = ResourceTree(root_name="org")
        tree.define("id", required=True)
        tree.create("/org/team1")  # Missing id
        tree.create("/org/team2", attributes={"id": "t2"})

        errors = tree.validate_all(path="/org/team2")

        # Only team2 subtree checked, and it's valid
        assert errors == {}

    def test_is_valid_returns_bool(self):
        """is_valid() returns True if no validation errors."""
        tree = ResourceTree(root_name="config")
        tree.define("port", type_=int, required=True)

        assert tree.is_valid() is False

        tree.root.set_attribute("port", 8080)
        assert tree.is_valid() is True


class TestValidationSummary:
    """Test validation summary output."""

    def test_validation_summary(self):
        """validation_summary() returns human-readable report."""
        tree = ResourceTree(root_name="config")
        tree.define("api_key", type_=str, required=True, description="API key for auth")
        tree.create("/config/service")

        summary = tree.validation_summary()

        assert "api_key" in summary
        assert "/config" in summary
        assert "/config/service" in summary
