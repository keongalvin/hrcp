"""Tests for documentation examples.

These tests ensure that all code examples in the documentation work correctly.
Each test corresponds to examples from specific documentation pages.
"""

import pytest

from hrcp import PropagationMode
from hrcp import Resource
from hrcp import ResourceTree
from hrcp import get_value


class TestReadmeExamples:
    """Tests for README.md examples."""

    def test_quick_example(self):
        """Test the quick example from README."""
        # Build a hierarchy
        tree = ResourceTree(root_name="platform")
        tree.root.set_attribute("timeout", 30)
        tree.root.set_attribute("env", "prod")

        tree.create("/platform/us-east/api", attributes={"timeout": 60})
        tree.create("/platform/us-east/db")
        tree.create("/platform/eu-west/api")

        # Inheritance: values flow DOWN
        api = tree.get("/platform/us-east/api")
        timeout = get_value(api, "timeout", PropagationMode.DOWN)
        assert timeout == 60  # local override

        db = tree.get("/platform/us-east/db")
        timeout = get_value(db, "timeout", PropagationMode.DOWN)
        assert timeout == 30  # inherited from root

        # Provenance: know where it came from
        prov = get_value(db, "timeout", PropagationMode.DOWN, with_provenance=True)
        assert prov.value == 30
        assert prov.source_path == "/platform"

    def test_down_propagation(self):
        """Test DOWN propagation example from README."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("tier", "premium")
        tree.create("/org/team/project")

        project = tree.get("/org/team/project")
        tier = get_value(project, "tier", PropagationMode.DOWN)
        assert tier == "premium"

    def test_up_propagation(self):
        """Test UP propagation example from README."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team1", attributes={"headcount": 5})
        tree.create("/org/team2", attributes={"headcount": 8})

        counts = get_value(tree.root, "headcount", PropagationMode.UP)
        assert sorted(counts) == [5, 8]

    def test_merge_down_propagation(self):
        """Test MERGE_DOWN propagation example from README."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("config", {"db": {"host": "localhost", "port": 5432}})
        tree.create(
            "/org/prod", attributes={"config": {"db": {"host": "prod.db.internal"}}}
        )

        prod = tree.get("/org/prod")
        config = get_value(prod, "config", PropagationMode.MERGE_DOWN)
        assert config == {"db": {"host": "prod.db.internal", "port": 5432}}


class TestWildcardExamples:
    """Tests for docs/guide/wildcards.md examples."""

    def test_single_segment_wildcard(self):
        """Test single wildcard (*) example."""
        tree = ResourceTree(root_name="platform")
        tree.create("/platform/us-east/api")
        tree.create("/platform/us-west/api")
        tree.create("/platform/eu-west/api")
        tree.create("/platform/us-east/db")

        # Match all regions' api services
        results = tree.query("/platform/*/api")
        paths = [r.path for r in results]

        assert "/platform/us-east/api" in paths
        assert "/platform/us-west/api" in paths
        assert "/platform/eu-west/api" in paths
        assert "/platform/us-east/db" not in paths
        assert len(results) == 3

    def test_multiple_single_wildcards(self):
        """Test multiple single wildcards."""
        tree = ResourceTree(root_name="platform")
        tree.create("/platform/us-east/api")
        tree.create("/platform/us-east/db")
        tree.create("/platform/us-west/api")

        # Match all services in all regions
        results = tree.query("/platform/*/*")
        assert len(results) == 3

    def test_multi_segment_wildcard(self):
        """Test double wildcard (**) example."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/eng/platform/api")
        tree.create("/org/eng/platform/db")
        tree.create("/org/eng/mobile/ios")
        tree.create("/org/sales/crm")

        # Match all resources under /org/eng at any depth
        results = tree.query("/org/eng/**")
        paths = [r.path for r in results]

        assert "/org/eng" in paths
        assert "/org/eng/platform" in paths
        assert "/org/eng/platform/api" in paths
        assert "/org/eng/platform/db" in paths
        assert "/org/eng/mobile" in paths
        assert "/org/eng/mobile/ios" in paths
        assert "/org/sales/crm" not in paths

    def test_double_wildcard_with_suffix(self):
        """Test double wildcard with suffix pattern."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/eng/platform/api")
        tree.create("/org/sales/api")

        # Match all 'api' resources anywhere in the tree
        results = tree.query("/org/**/api")
        paths = [r.path for r in results]

        assert "/org/eng/platform/api" in paths
        assert "/org/sales/api" in paths
        assert len(results) == 2

    def test_query_values(self):
        """Test query_values example."""
        tree = ResourceTree(root_name="platform")
        tree.create("/platform/us-east/api", attributes={"timeout": 60})
        tree.create("/platform/us-west/api", attributes={"timeout": 30})
        tree.create("/platform/eu-west/api", attributes={"timeout": 45})

        timeouts = tree.query_values("/platform/*/api", "timeout", PropagationMode.NONE)
        assert sorted(timeouts) == [30, 45, 60]


class TestProvenanceExamples:
    """Tests for docs/guide/provenance.md examples."""

    def test_basic_provenance(self):
        """Test basic provenance example."""
        tree = ResourceTree(root_name="platform")
        tree.root.set_attribute("timeout", 30)
        tree.create("/platform/us-east/api", attributes={"timeout": 60})
        tree.create("/platform/us-east/db")

        db = tree.get("/platform/us-east/db")
        prov = get_value(db, "timeout", PropagationMode.DOWN, with_provenance=True)

        assert prov.value == 30
        assert prov.source_path == "/platform"
        assert prov.mode == PropagationMode.DOWN

    def test_down_provenance_closest_ancestor(self):
        """Test DOWN provenance finds closest ancestor."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("env", "prod")
        tree.create("/org/team", attributes={"env": "staging"})
        tree.create("/org/team/project")

        project = tree.get("/org/team/project")
        prov = get_value(project, "env", PropagationMode.DOWN, with_provenance=True)

        assert prov.value == "staging"
        assert prov.source_path == "/org/team"

    def test_none_provenance(self):
        """Test NONE provenance for local values."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("env", "prod")
        tree.create("/org/team/project")

        project = tree.get("/org/team/project")
        prov = get_value(project, "env", PropagationMode.NONE, with_provenance=True)

        # When attribute not found locally, get_value returns None (not Provenance)
        assert prov is None

    def test_up_provenance_contributing_paths(self):
        """Test UP provenance with contributing_paths."""
        tree = ResourceTree(root_name="company")
        tree.create("/company/eng", attributes={"budget": 100000})
        tree.create("/company/sales", attributes={"budget": 50000})

        prov = get_value(tree.root, "budget", PropagationMode.UP, with_provenance=True)

        assert sorted(prov.value) == [50000, 100000]
        assert prov.source_path == "/company"
        assert "/company/eng" in prov.contributing_paths
        assert "/company/sales" in prov.contributing_paths

    def test_merge_down_key_sources(self):
        """Test MERGE_DOWN provenance with key_sources."""
        tree = ResourceTree(root_name="platform")
        tree.root.set_attribute("config", {"timeout": 30, "retries": 3})
        tree.create("/platform/prod", attributes={"config": {"timeout": 60}})

        prod = tree.get("/platform/prod")
        prov = get_value(
            prod, "config", PropagationMode.MERGE_DOWN, with_provenance=True
        )

        assert prov.value == {"timeout": 60, "retries": 3}
        assert prov.key_sources["timeout"] == "/platform/prod"
        assert prov.key_sources["retries"] == "/platform"


class TestPropagationExamples:
    """Tests for docs/guide/propagation.md examples."""

    def test_down_inheritance_chain(self):
        """Test DOWN propagation through inheritance chain."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("timeout", 30)
        tree.create("/org/team", attributes={"timeout": 60})
        tree.create("/org/team/project")
        tree.create("/org/team/project/service")

        root_timeout = get_value(tree.root, "timeout", PropagationMode.DOWN)
        assert root_timeout == 30

        team_timeout = get_value(tree.get("/org/team"), "timeout", PropagationMode.DOWN)
        assert team_timeout == 60

        project_timeout = get_value(
            tree.get("/org/team/project"), "timeout", PropagationMode.DOWN
        )
        assert project_timeout == 60

        service_timeout = get_value(
            tree.get("/org/team/project/service"), "timeout", PropagationMode.DOWN
        )
        assert service_timeout == 60

    def test_up_aggregation(self):
        """Test UP aggregation from descendants."""
        tree = ResourceTree(root_name="company")
        tree.create("/company/eng", attributes={"headcount": 50})
        tree.create("/company/eng/platform", attributes={"headcount": 15})
        tree.create("/company/eng/mobile", attributes={"headcount": 10})
        tree.create("/company/sales", attributes={"headcount": 30})

        company = tree.root
        headcounts = get_value(company, "headcount", PropagationMode.UP)
        assert sorted(headcounts) == [10, 15, 30, 50]

        eng = tree.get("/company/eng")
        eng_headcounts = get_value(eng, "headcount", PropagationMode.UP)
        assert sorted(eng_headcounts) == [10, 15, 50]

    def test_merge_down_deep_merge(self):
        """Test MERGE_DOWN deep dictionary merge."""
        tree = ResourceTree(root_name="platform")
        tree.root.set_attribute(
            "config",
            {
                "database": {"host": "localhost", "port": 5432, "pool_size": 10},
                "cache": {"enabled": True, "ttl": 300},
            },
        )
        tree.create(
            "/platform/prod",
            attributes={
                "config": {"database": {"host": "prod.db.internal", "pool_size": 50}},
            },
        )

        prod = tree.get("/platform/prod")
        config = get_value(prod, "config", PropagationMode.MERGE_DOWN)

        assert config == {
            "database": {"host": "prod.db.internal", "port": 5432, "pool_size": 50},
            "cache": {"enabled": True, "ttl": 300},
        }

    def test_none_local_only(self):
        """Test NONE returns only local value."""
        tree = ResourceTree(root_name="org")
        tree.root.set_attribute("global_id", "ORG-001")
        tree.create("/org/team")

        team = tree.get("/org/team")

        local = get_value(team, "global_id", PropagationMode.NONE)
        assert local is None

        inherited = get_value(team, "global_id", PropagationMode.DOWN)
        assert inherited == "ORG-001"


class TestSerializationExamples:
    """Tests for docs/guide/serialization.md examples."""

    def test_to_dict_structure(self):
        """Test to_dict returns correct structure."""
        tree = ResourceTree(root_name="platform")
        tree.root.set_attribute("env", "prod")
        tree.create("/platform/api", attributes={"port": 8080})

        data = tree.to_dict()

        assert data["name"] == "platform"
        assert data["attributes"] == {"env": "prod"}
        assert "api" in data["children"]
        assert data["children"]["api"]["attributes"] == {"port": 8080}

    def test_from_dict_reconstruction(self):
        """Test from_dict reconstructs tree correctly."""
        data = {
            "name": "platform",
            "attributes": {"env": "prod"},
            "children": {
                "api": {
                    "name": "api",
                    "attributes": {"port": 8080},
                    "children": {},
                },
            },
        }

        tree = ResourceTree.from_dict(data)

        assert tree.root.name == "platform"
        assert tree.root.get_attribute("env") == "prod"
        api = tree.get("/platform/api")
        assert api is not None
        assert api.get_attribute("port") == 8080

    def test_roundtrip_serialization(self):
        """Test dict serialization roundtrip."""
        tree = ResourceTree(root_name="config")
        tree.root.set_attribute("version", "1.0")
        tree.create("/config/db", attributes={"host": "localhost", "port": 5432})
        tree.create("/config/cache", attributes={"enabled": True})

        # Roundtrip
        data = tree.to_dict()
        restored = ResourceTree.from_dict(data)

        assert restored.root.get_attribute("version") == "1.0"
        assert restored.get("/config/db").get_attribute("host") == "localhost"
        assert restored.get("/config/cache").get_attribute("enabled") is True


class TestConceptsExamples:
    """Tests for docs/guide/concepts.md examples."""

    def test_resource_properties(self):
        """Test Resource properties example."""
        tree = ResourceTree(root_name="platform")
        tree.create("/platform/us-east/api")

        api = tree.get("/platform/us-east/api")

        assert api.name == "api"
        assert api.path == "/platform/us-east/api"
        assert api.parent.name == "us-east"
        assert api.children == {}

    def test_automatic_parent_creation(self):
        """Test automatic parent creation."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team/project/env")

        # Intermediate resources are created
        assert tree.get("/org/team") is not None
        assert tree.get("/org/team/project") is not None
        assert tree.get("/org/team/project/env") is not None

    def test_attribute_operations(self):
        """Test attribute operations."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team")
        resource = tree.get("/org/team")

        resource.set_attribute("budget", 50000)
        resource.set_attribute("tier", "premium")
        resource.set_attribute("config", {"debug": True})

        assert resource.get_attribute("budget") == 50000
        assert resource.get_attribute("unknown") is None

    def test_putting_it_together(self):
        """Test the 'Putting It Together' example."""
        tree = ResourceTree(root_name="company")

        tree.root.set_attribute("env", "production")
        tree.root.set_attribute("log_level", "INFO")

        tree.create("/company/engineering", attributes={"log_level": "DEBUG"})
        tree.create("/company/engineering/api")

        api = tree.get("/company/engineering/api")

        env = get_value(api, "env", PropagationMode.DOWN)
        assert env == "production"

        log_level = get_value(api, "log_level", PropagationMode.DOWN)
        assert log_level == "DEBUG"

        prov = get_value(api, "log_level", PropagationMode.DOWN, with_provenance=True)
        assert prov.value == "DEBUG"
        assert prov.source_path == "/company/engineering"


class TestUseCaseExamples:
    """Tests for selected use case examples from docs/examples/."""

    def test_multi_tenant_saas(self):
        """Test multi-tenant SaaS example."""
        tree = ResourceTree(root_name="platform")

        tree.root.set_attribute("timeout", 30)
        tree.root.set_attribute("max_requests_per_minute", 1000)
        tree.root.set_attribute(
            "features",
            {
                "dark_mode": False,
                "beta_features": False,
                "ai_assist": False,
            },
        )

        tree.create(
            "/platform/acme-corp",
            attributes={
                "tier": "enterprise",
                "max_requests_per_minute": 10000,
                "features": {"ai_assist": True},
            },
        )
        tree.create("/platform/acme-corp/analytics", attributes={"timeout": 120})

        analytics = tree.get("/platform/acme-corp/analytics")

        timeout = get_value(analytics, "timeout", PropagationMode.DOWN)
        assert timeout == 120

        rate_limit = get_value(
            analytics, "max_requests_per_minute", PropagationMode.DOWN
        )
        assert rate_limit == 10000

        features = get_value(analytics, "features", PropagationMode.MERGE_DOWN)
        assert features == {
            "dark_mode": False,
            "beta_features": False,
            "ai_assist": True,
        }

    def test_feature_flags(self):
        """Test feature flags example."""
        tree = ResourceTree(root_name="features")

        tree.root.set_attribute("new_checkout", False)
        tree.root.set_attribute("dark_mode", False)

        tree.create(
            "/features/beta",
            attributes={
                "new_checkout": True,
                "dark_mode": True,
            },
        )
        tree.create("/features/beta/user-123")
        tree.create("/features/beta/user-456", attributes={"dark_mode": False})

        user123 = tree.get("/features/beta/user-123")
        assert get_value(user123, "new_checkout", PropagationMode.DOWN) is True
        assert get_value(user123, "dark_mode", PropagationMode.DOWN) is True

        user456 = tree.get("/features/beta/user-456")
        assert get_value(user456, "new_checkout", PropagationMode.DOWN) is True
        assert get_value(user456, "dark_mode", PropagationMode.DOWN) is False

    def test_budget_rollup(self):
        """Test budget rollup example."""
        tree = ResourceTree(root_name="company")

        tree.create("/company/engineering", attributes={"budget": 500000})
        tree.create("/company/engineering/platform", attributes={"budget": 200000})
        tree.create("/company/engineering/mobile", attributes={"budget": 150000})
        tree.create("/company/sales", attributes={"budget": 300000})

        eng_budgets = get_value(
            tree.get("/company/engineering"), "budget", PropagationMode.UP
        )
        assert sum(eng_budgets) == 850000  # 500000 + 200000 + 150000

        all_budgets = get_value(tree.root, "budget", PropagationMode.UP)
        assert sum(all_budgets) == 1150000  # 500000 + 200000 + 150000 + 300000

    def test_kubernetes_namespaces(self):
        """Test Kubernetes namespaces example."""
        tree = ResourceTree(root_name="cluster")

        tree.root.set_attribute("resource_quota", {"cpu": "100", "memory": "100Gi"})
        tree.root.set_attribute("network_policy", "deny-all")

        tree.create(
            "/cluster/prod",
            attributes={
                "resource_quota": {"cpu": "500", "memory": "500Gi"},
            },
        )
        tree.create(
            "/cluster/dev",
            attributes={
                "resource_quota": {"cpu": "50"},
                "network_policy": "allow-all",
            },
        )
        tree.create("/cluster/prod/team-api")
        tree.create("/cluster/dev/team-api")

        prod_api = tree.get("/cluster/prod/team-api")
        prod_quota = get_value(prod_api, "resource_quota", PropagationMode.MERGE_DOWN)
        assert prod_quota["cpu"] == "500"
        assert prod_quota["memory"] == "500Gi"

        dev_api = tree.get("/cluster/dev/team-api")
        dev_quota = get_value(dev_api, "resource_quota", PropagationMode.MERGE_DOWN)
        assert dev_quota["cpu"] == "50"
        assert dev_quota["memory"] == "100Gi"  # inherited from cluster

        dev_network = get_value(dev_api, "network_policy", PropagationMode.DOWN)
        assert dev_network == "allow-all"


class TestTroubleshootingExamples:
    """Tests for docs/guide/troubleshooting.md examples."""

    def test_path_must_start_with_root(self):
        """Test path validation error."""
        tree = ResourceTree(root_name="platform")

        with pytest.raises(ValueError, match="Path must start with '/platform'"):
            tree.create("/wrong/path")

    def test_resource_already_exists(self):
        """Test duplicate resource error."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team")

        with pytest.raises(ValueError, match="Resource already exists"):
            tree.create("/org/team")

    def test_name_cannot_contain_slash(self):
        """Test name validation error."""
        with pytest.raises(ValueError, match="name cannot contain '/'"):
            Resource(name="my/resource")

    def test_check_existence_before_create(self):
        """Test checking existence before creating."""
        tree = ResourceTree(root_name="org")
        tree.create("/org/team")

        existing = tree.get("/org/team")
        if existing is None:
            tree.create("/org/team", attributes={"new": True})
        else:
            existing.set_attribute("updated", True)

        assert tree.get("/org/team").get_attribute("updated") is True
