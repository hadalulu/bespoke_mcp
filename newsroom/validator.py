"""Small, deterministic validator for declared components of a proposed use."""

from __future__ import annotations

from newsroom.models import EditorialPackage, ProposedUse, ValidationResult, Violation, build_effective_policy

CONFIDENCE_ORDER = {
    "unverified": 0,
    "alleged": 1,
    "disputed": 1,
    "developing": 2,
    "estimated": 2,
    "confirmed": 3,
}


def validate_proposed_use(story: EditorialPackage, proposed: ProposedUse) -> ValidationResult:
    """Validate structured declarations; this is demonstrative, not semantic NLP."""
    effective = build_effective_policy(story)
    violations: list[Violation] = []
    facts = {fact.id: fact for fact in story.verified_facts}
    evidence = {item.description.casefold() for item in story.sources_evidence}
    quotes = {quote.id: quote for quote in story.quotes}

    for disclosure in story.required_disclosures:
        if disclosure.required_when == "all_uses" and disclosure.id not in proposed.disclosure_ids:
            violations.append(Violation(code="MISSING_REQUIRED_DISCLOSURE", policy_code="INCLUDE_REQUIRED_DISCLOSURES", item_id=disclosure.id, message=f"The proposed use omits required disclosure {disclosure.id}."))

    prohibited = set(story.key_framing_boundaries.not_allowed)
    for framing_id in sorted(set(proposed.framing_ids) & prohibited):
        violations.append(Violation(code="DISALLOWED_FRAMING", policy_code="USE_DISALLOWED_FRAMING", item_id=framing_id, message=f"The proposed use declares prohibited framing {framing_id}."))

    for fact_id in proposed.fact_ids:
        if fact_id not in facts:
            violations.append(Violation(code="INVENTED_FACT", policy_code="INVENT_FACTS", item_id=fact_id, message=f"Fact {fact_id} is not in the editorial package."))
    known_fact_texts = {fact.text.casefold() for fact in story.verified_facts} | evidence
    for claim in proposed.claims:
        if claim.casefold() not in known_fact_texts:
            violations.append(Violation(code="INVENTED_FACT", policy_code="INVENT_FACTS", message=f"Claim is not supported by the package: {claim}"))

    for used_quote in proposed.quotes:
        source = quotes.get(used_quote.quote_id or "")
        if source is None:
            violations.append(Violation(code="FABRICATED_QUOTE", policy_code="INVENT_QUOTES", item_id=used_quote.quote_id, message=f"Direct quote attributed to {used_quote.speaker} is not in the package."))
        elif used_quote.presented_as_direct and (used_quote.text != source.exact_text or used_quote.speaker != source.speaker):
            violations.append(Violation(code="ALTERED_QUOTE", policy_code="MATERIALLY_ALTER_QUOTES", item_id=source.id, message=f"Quote {source.id} does not exactly match its verified text and speaker."))

    included = set(proposed.fact_ids)
    for fact in story.verified_facts:
        if fact.material and fact.id not in included:
            violations.append(Violation(code="MATERIAL_OMISSION", policy_code="CREATE_MISLEADING_OMISSIONS", item_id=fact.id, message=f"The proposed use omits material fact {fact.id}."))

    confidence = {item.subject: item.level for item in story.editorial_confidence}
    for subject, declared in proposed.confidence.items():
        source_level = confidence.get(subject)
        if source_level and CONFIDENCE_ORDER.get(declared, 99) > CONFIDENCE_ORDER[source_level]:
            violations.append(Violation(code="OVERSTATED_CONFIDENCE", policy_code="OVERSTATE_CERTAINTY", item_id=subject, message=f"{subject} is {source_level}, but the proposed use represents it as {declared}."))

    restrictions = set(story.story_usage_policy.additional_restrictions) if story.story_usage_policy else set()
    for action in sorted(set(proposed.policy_actions) & restrictions):
        violations.append(Violation(code="STORY_POLICY_VIOLATION", policy_code=action, item_id=action, message=f"The proposed use performs story-prohibited action {action}."))

    return ValidationResult(compliant=not violations, violations=violations, checked_against=effective)
