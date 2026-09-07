from newsroom.models import build_effective_policy, load_editorial_package, load_newsroom_policy


def test_newsroom_policy_loads_with_descriptions() -> None:
    policy = load_newsroom_policy()
    assert policy.version == "1.0"
    assert set(policy.must + policy.must_not) <= {rule.code for rule in policy.rules}


def test_effective_policy_always_contains_newsroom_rules() -> None:
    newsroom = load_newsroom_policy()
    for story_id in ("story_001", "story_002"):
        effective = build_effective_policy(load_editorial_package(story_id), newsroom)
        assert set(newsroom.must) <= set(effective.must)
        assert set(newsroom.must_not) <= set(effective.must_not)


def test_story_rules_are_added_without_removing_newsroom_rules() -> None:
    newsroom = load_newsroom_policy()
    effective = build_effective_policy(load_editorial_package("story_002"), newsroom)
    assert "IDENTIFY_ALLEGATIONS_AS_ALLEGATIONS" in effective.must
    assert "DO_NOT_IDENTIFY_MINOR" in effective.must_not
    assert effective.newsroom_policy_version == "1.0"
    assert effective.story_policy_version == "1.0"
    assert len(effective.must) >= len(newsroom.must)
    assert len(effective.must_not) >= len(newsroom.must_not)
