import pytest

from newsroom.models import EditorialPackage, StoryUsagePolicy, list_editorial_packages


def test_editorial_packages_load_and_have_required_fields() -> None:
    packages = list_editorial_packages()
    assert len(packages) >= 2
    required = {
        "title", "verified_facts", "sources_evidence", "key_framing_boundaries",
        "required_disclosures", "quotes", "chronology", "editorial_confidence",
        "other_editorial_judgment", "media",
    }
    for package in packages:
        assert required <= set(EditorialPackage.model_fields)


def test_story_policy_is_optional() -> None:
    packages = list_editorial_packages()
    assert any(package.story_usage_policy is None for package in packages)
    assert any(package.story_usage_policy is not None for package in packages)


def test_story_policy_rejects_weakening_codes() -> None:
    with pytest.raises(ValueError, match="add or tighten"):
        StoryUsagePolicy(version="1", additional_requirements=["REMOVE_REQUIRED_DISCLOSURE"])
