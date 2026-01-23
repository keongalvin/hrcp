"""Tests for HRCP search/filter functionality.

Uses pure data-driven approach - no mocking or monkeypatching.
"""

from hypothesis import given
from hypothesis import strategies as st

from hrcp import ResourceTree

# Strategy for valid resource names
valid_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)


class TestFindByAttribute:
    """Test finding resources by attribute values."""

    @given(
        root=valid_name,
        name1=valid_name,
        name2=valid_name,
        name3=valid_name,
        role1=st.text(min_size=1, max_size=10),
        role2=st.text(min_size=1, max_size=10),
    )
    def test_find_by_exact_value(self, root, name1, name2, name3, role1, role2):
        """find() returns resources with matching attribute value."""
        # Ensure unique names and different roles
        names = [name1]
        if name2 not in names:
            names.append(name2)
        else:
            names.append(name2 + "2")
        if name3 not in names:
            names.append(name3)
        else:
            names.append(name3 + "3")
        if role1 == role2:
            role2 = role2 + "x"

        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{names[0]}", attributes={"role": role1})
        tree.create(f"/{root}/{names[1]}", attributes={"role": role2})
        tree.create(f"/{root}/{names[2]}", attributes={"role": role1})

        results = tree.find(role=role1)

        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {names[0], names[2]}

    @given(root=valid_name, name1=valid_name, name2=valid_name, name3=valid_name)
    def test_find_by_multiple_attributes(self, root, name1, name2, name3):
        """find() with multiple attrs returns resources matching all."""
        names = [name1]
        for n in [name2, name3]:
            if n in names:
                names.append(n + str(len(names)))
            else:
                names.append(n)

        tree = ResourceTree(root_name=root)
        tree.create(
            f"/{root}/{names[0]}", attributes={"role": "dev", "team": "backend"}
        )
        tree.create(
            f"/{root}/{names[1]}", attributes={"role": "dev", "team": "frontend"}
        )
        tree.create(f"/{root}/{names[2]}", attributes={"role": "qa", "team": "backend"})

        results = tree.find(role="dev", team="backend")

        assert len(results) == 1
        assert results[0].name == names[0]

    @given(
        root=valid_name,
        name=valid_name,
        role=st.text(min_size=1, max_size=10),
        search_role=st.text(min_size=1, max_size=10),
    )
    def test_find_returns_empty_when_no_match(self, root, name, role, search_role):
        """find() returns empty list when no resources match."""
        if role == search_role:
            search_role = search_role + "x"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{name}", attributes={"role": role})

        results = tree.find(role=search_role)

        assert results == []

    @given(
        root=valid_name,
        team1=valid_name,
        team2=valid_name,
        member1=valid_name,
        member2=valid_name,
    )
    def test_find_in_subtree(self, root, team1, team2, member1, member2):
        """find() with path restricts search to subtree."""
        if team1 == team2:
            team2 = team2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{team1}/{member1}", attributes={"level": "senior"})
        tree.create(f"/{root}/{team2}/{member2}", attributes={"level": "senior"})

        results = tree.find(level="senior", path=f"/{root}/{team1}")

        assert len(results) == 1
        assert results[0].name == member1


class TestFindFirst:
    """Test finding first matching resource."""

    @given(root=valid_name, name1=valid_name, name2=valid_name)
    def test_find_first_returns_single_result(self, root, name1, name2):
        """find_first() returns first matching resource or None."""
        if name1 == name2:
            name2 = name2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{name1}", attributes={"active": True})
        tree.create(f"/{root}/{name2}", attributes={"active": False})

        result = tree.find_first(active=True)

        assert result is not None
        assert result.name == name1

    @given(root=valid_name, name=valid_name)
    def test_find_first_returns_none_when_no_match(self, root, name):
        """find_first() returns None when no resources match."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{name}", attributes={"active": True})

        result = tree.find_first(active=False)

        assert result is None


class TestFilter:
    """Test filtering resources with predicates."""

    @given(
        root=valid_name,
        name1=valid_name,
        name2=valid_name,
        name3=valid_name,
        age1=st.integers(min_value=30, max_value=50),
        age2=st.integers(min_value=20, max_value=29),
        age3=st.integers(min_value=30, max_value=50),
    )
    def test_filter_with_predicate(self, root, name1, name2, name3, age1, age2, age3):
        """filter() returns resources where predicate returns True."""
        names = [name1]
        for n in [name2, name3]:
            if n in names:
                names.append(n + str(len(names)))
            else:
                names.append(n)

        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{names[0]}", attributes={"age": age1})
        tree.create(f"/{root}/{names[1]}", attributes={"age": age2})
        tree.create(f"/{root}/{names[2]}", attributes={"age": age3})

        results = tree.filter(lambda r: r.attributes.get("age", 0) >= 30)

        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {names[0], names[2]}

    @given(
        root=valid_name,
        team1=valid_name,
        team2=valid_name,
        member1=valid_name,
        member2=valid_name,
    )
    def test_filter_with_path(self, root, team1, team2, member1, member2):
        """filter() with path restricts to subtree."""
        if team1 == team2:
            team2 = team2 + "2"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{team1}/{member1}", attributes={"active": True})
        tree.create(f"/{root}/{team2}/{member2}", attributes={"active": True})

        results = tree.filter(
            lambda r: r.attributes.get("active"), path=f"/{root}/{team1}"
        )

        assert len(results) == 1


class TestExists:
    """Test checking if resources with criteria exist."""

    @given(root=valid_name, name=valid_name, role=st.text(min_size=1, max_size=10))
    def test_exists_returns_true_when_found(self, root, name, role):
        """exists() returns True when matching resource found."""
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{name}", attributes={"role": role})

        assert tree.exists(role=role) is True

    @given(
        root=valid_name,
        name=valid_name,
        role=st.text(min_size=1, max_size=10),
        search_role=st.text(min_size=1, max_size=10),
    )
    def test_exists_returns_false_when_not_found(self, root, name, role, search_role):
        """exists() returns False when no matching resource."""
        if role == search_role:
            search_role = search_role + "x"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{name}", attributes={"role": role})

        assert tree.exists(role=search_role) is False


class TestCount:
    """Test counting resources with criteria."""

    @given(
        root=valid_name,
        name1=valid_name,
        name2=valid_name,
        name3=valid_name,
        type1=st.text(min_size=1, max_size=10),
        type2=st.text(min_size=1, max_size=10),
    )
    def test_count_matching(self, root, name1, name2, name3, type1, type2):
        """count() returns number of matching resources."""
        names = [name1]
        for n in [name2, name3]:
            if n in names:
                names.append(n + str(len(names)))
            else:
                names.append(n)
        if type1 == type2:
            type2 = type2 + "x"

        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/{names[0]}", attributes={"type": type1})
        tree.create(f"/{root}/{names[1]}", attributes={"type": type1})
        tree.create(f"/{root}/{names[2]}", attributes={"type": type2})

        assert tree.count(type=type1) == 2
        assert tree.count(type=type2) == 1
        assert tree.count(type="nonexistent") == 0


class TestSearchWithInvalidPath:
    """Test search functions with invalid paths."""

    @given(root=valid_name, fake=valid_name)
    def test_find_with_invalid_path_returns_empty(self, root, fake):
        """find() with invalid path returns empty list."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/child", attributes={"x": 1})

        results = tree.find(path=f"/{fake}", x=1)

        assert results == []

    @given(root=valid_name, fake=valid_name)
    def test_find_first_with_invalid_path_returns_none(self, root, fake):
        """find_first() with invalid path returns None."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/child", attributes={"x": 1})

        result = tree.find_first(path=f"/{fake}", x=1)

        assert result is None

    @given(root=valid_name, fake=valid_name)
    def test_filter_with_invalid_path_returns_empty(self, root, fake):
        """filter() with invalid path returns empty list."""
        if root == fake:
            fake = fake + "x"
        tree = ResourceTree(root_name=root)
        tree.create(f"/{root}/child", attributes={"x": 1})

        results = tree.filter(lambda r: True, path=f"/{fake}")

        assert results == []
