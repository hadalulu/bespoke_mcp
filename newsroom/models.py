"""Typed models and JSON loading for newsroom policies and editorial packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PACKAGE_DIR = Path(__file__).parent
POLICY_PATH = PACKAGE_DIR / "policies" / "newsroom_policy.json"
STORIES_DIR = PACKAGE_DIR / "stories"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PolicyRule(StrictModel):
    code: str
    description: str


class NewsroomPolicy(StrictModel):
    id: str
    version: str
    must: list[str]
    must_not: list[str]
    rules: list[PolicyRule]

    @model_validator(mode="after")
    def descriptions_cover_codes(self) -> "NewsroomPolicy":
        described = {rule.code for rule in self.rules}
        missing = (set(self.must) | set(self.must_not)) - described
        if missing:
            raise ValueError(f"Missing descriptions for policy codes: {sorted(missing)}")
        return self


class Evidence(StrictModel):
    id: str
    description: str
    provenance: str


class Fact(StrictModel):
    id: str
    text: str
    material: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Literal["confirmed", "developing", "disputed", "alleged", "estimated", "unverified"] = "confirmed"


class FramingBoundaries(StrictModel):
    allowed: list[str] = Field(default_factory=list)
    not_allowed: list[str] = Field(default_factory=list)


class Disclosure(StrictModel):
    id: str
    text: str
    required_when: str = "all_uses"


class Quote(StrictModel):
    id: str
    speaker: str
    exact_text: str
    source_evidence_id: str
    verified: bool = True


class ChronologyEntry(StrictModel):
    date: str
    event: str


class ConfidenceItem(StrictModel):
    subject: str
    level: Literal["confirmed", "developing", "disputed", "alleged", "estimated", "unverified"]
    note: str


class MediaItem(StrictModel):
    id: str
    kind: str
    description: str
    provenance: str
    attribution: str


class StoryUsagePolicy(StrictModel):
    version: str
    additional_requirements: list[str] = Field(default_factory=list)
    additional_restrictions: list[str] = Field(default_factory=list)
    rule_descriptions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def no_override_language(self) -> "StoryUsagePolicy":
        codes = self.additional_requirements + self.additional_restrictions
        if any(code.startswith(("REMOVE_", "ALLOW_", "OVERRIDE_")) for code in codes):
            raise ValueError("Story policy may only add or tighten constraints")
        return self


class EditorialPackage(StrictModel):
    id: str
    title: str
    verified_facts: list[Fact]
    sources_evidence: list[Evidence]
    key_framing_boundaries: FramingBoundaries
    required_disclosures: list[Disclosure]
    quotes: list[Quote]
    chronology: list[ChronologyEntry]
    editorial_confidence: list[ConfidenceItem]
    other_editorial_judgment: list[str]
    media: list[MediaItem]
    story_usage_policy: StoryUsagePolicy | None = None


class EffectivePolicy(StrictModel):
    newsroom_policy_id: str
    newsroom_policy_version: str
    story_policy_version: str | None
    must: list[str]
    must_not: list[str]
    rule_descriptions: dict[str, str]


class ProposedQuote(StrictModel):
    quote_id: str | None = None
    speaker: str
    text: str
    presented_as_direct: bool = True


class ProposedUse(StrictModel):
    text: str
    fact_ids: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    disclosure_ids: list[str] = Field(default_factory=list)
    framing_ids: list[str] = Field(default_factory=list)
    quotes: list[ProposedQuote] = Field(default_factory=list)
    confidence: dict[str, str] = Field(default_factory=dict)
    policy_actions: list[str] = Field(default_factory=list)


class Violation(StrictModel):
    code: str
    message: str
    policy_code: str
    item_id: str | None = None


class ValidationResult(StrictModel):
    compliant: bool
    violations: list[Violation]
    checked_against: EffectivePolicy


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_newsroom_policy() -> NewsroomPolicy:
    return NewsroomPolicy.model_validate(_load_json(POLICY_PATH))


def list_editorial_packages() -> list[EditorialPackage]:
    return [EditorialPackage.model_validate(_load_json(path)) for path in sorted(STORIES_DIR.glob("*.json"))]


def load_editorial_package(story_id: str) -> EditorialPackage:
    path = STORIES_DIR / f"{story_id}.json"
    if not path.is_file() or path.parent != STORIES_DIR:
        raise ValueError(f"Unknown story_id: {story_id}")
    return EditorialPackage.model_validate(_load_json(path))


def build_effective_policy(story: EditorialPackage, newsroom: NewsroomPolicy | None = None) -> EffectivePolicy:
    newsroom = newsroom or load_newsroom_policy()
    must = list(newsroom.must)
    must_not = list(newsroom.must_not)
    descriptions = {rule.code: rule.description for rule in newsroom.rules}
    story_version = None
    if story.story_usage_policy:
        story_version = story.story_usage_policy.version
        must.extend(code for code in story.story_usage_policy.additional_requirements if code not in must)
        must_not.extend(code for code in story.story_usage_policy.additional_restrictions if code not in must_not)
        descriptions.update(story.story_usage_policy.rule_descriptions)
    return EffectivePolicy(
        newsroom_policy_id=newsroom.id,
        newsroom_policy_version=newsroom.version,
        story_policy_version=story_version,
        must=must,
        must_not=must_not,
        rule_descriptions=descriptions,
    )
