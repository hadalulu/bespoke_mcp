"""Predefined proposed uses that exercise the validator."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _ferry_base() -> dict[str, Any]:
    return {
        "text": "Bellwether City's six-month ferry pilot began after weather delayed drills. An 18% emissions reduction is projected, not measured.",
        "fact_ids": ["fact_001", "fact_002", "fact_004"],
        "claims": [],
        "disclosure_ids": ["disc_001"],
        "framing_ids": ["public_transit_pilot", "weather_delayed_launch", "unmeasured_emissions_goal"],
        "quotes": [],
        "confidence": {"pilot_launch": "confirmed", "emissions_reduction": "estimated"},
        "policy_actions": [],
    }


def _school_base() -> dict[str, Any]:
    return {
        "text": "The board opened a review into an unsubstantiated allegation about attendance totals. No student is accused.",
        "fact_ids": ["fact_101", "fact_102", "fact_103"],
        "claims": [],
        "disclosure_ids": ["disc_101"],
        "framing_ids": ["independent_review", "unsubstantiated_attendance_allegation"],
        "quotes": [],
        "confidence": {"review_opened": "confirmed", "attendance_overstatement": "alleged"},
        "policy_actions": [],
    }


SCENARIOS: dict[str, dict[str, Any]] = {
    "allowed-neutral": {"label": "Allowed: neutral summary preserving facts and disclosure", "story_id": "story_001", "proposed_use": _ferry_base()},
    "allowed-short": {"label": "Allowed: shortened summary omitting non-material capacity", "story_id": "story_001", "proposed_use": _ferry_base()},
    "allowed-creative": {"label": "Allowed: newsletter-style transformation preserving constraints", "story_id": "story_001", "proposed_use": {**_ferry_base(), "text": "Harbor Notes: The ferry pilot is afloat after high winds delayed safety drills. The hoped-for 18% emissions cut remains an unmeasured projection."}},
}


def _add(name: str, label: str, story_id: str, mutate: Any) -> None:
    use = deepcopy(_school_base() if story_id == "story_002" else _ferry_base())
    mutate(use)
    SCENARIOS[name] = {"label": label, "story_id": story_id, "proposed_use": use}


_add("rejected-disclosure", "Rejected: required disclosure omitted", "story_001", lambda use: use["disclosure_ids"].clear())
_add("rejected-framing", "Rejected: disallowed framing introduced", "story_001", lambda use: use["framing_ids"].append("proven_emissions_success"))
_add("rejected-fact", "Rejected: fabricated fact", "story_001", lambda use: use["fact_ids"].append("fact_999"))
_add("rejected-quote", "Rejected: fabricated quote", "story_001", lambda use: use["quotes"].append({"speaker": "The mayor", "text": "This will solve traffic.", "presented_as_direct": True}))
_add("rejected-altered-quote", "Rejected: verified quote materially altered", "story_001", lambda use: use["quotes"].append({"quote_id": "quote_001", "speaker": "Transit director Mira Sol", "text": "The pilot proves this route works.", "presented_as_direct": True}))
_add("rejected-confidence", "Rejected: uncertain information stated as established", "story_001", lambda use: use["confidence"].update({"emissions_reduction": "confirmed"}))
_add("rejected-omission", "Rejected: material fact omitted", "story_001", lambda use: use["fact_ids"].remove("fact_002"))
_add("rejected-story-policy", "Rejected: story-specific restriction violated", "story_002", lambda use: use["policy_actions"].append("DO_NOT_IDENTIFY_MINOR"))
