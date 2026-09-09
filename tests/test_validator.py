import pytest

from newsroom.models import ProposedUse, load_editorial_package
from newsroom.scenarios import SCENARIOS
from newsroom.validator import validate_proposed_use


def validate(name: str):
    scenario = SCENARIOS[name]
    story = load_editorial_package(scenario["story_id"])
    return validate_proposed_use(story, ProposedUse.model_validate(scenario["proposed_use"]))


@pytest.mark.parametrize("name", ["allowed-neutral", "allowed-short", "allowed-creative"])
def test_compliant_and_shortened_uses_pass(name: str) -> None:
    result = validate(name)
    assert result.compliant
    assert result.violations == []


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("rejected-disclosure", "MISSING_REQUIRED_DISCLOSURE"),
        ("rejected-framing", "DISALLOWED_FRAMING"),
        ("rejected-fact", "INVENTED_FACT"),
        ("rejected-quote", "FABRICATED_QUOTE"),
        ("rejected-altered-quote", "ALTERED_QUOTE"),
        ("rejected-omission", "MATERIAL_OMISSION"),
        ("rejected-confidence", "OVERSTATED_CONFIDENCE"),
        ("rejected-story-policy", "STORY_POLICY_VIOLATION"),
    ],
)
def test_rejected_scenarios_report_expected_violation(name: str, code: str) -> None:
    result = validate(name)
    assert not result.compliant
    assert code in {violation.code for violation in result.violations}
