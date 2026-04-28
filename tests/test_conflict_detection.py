import pytest

from claim_aware_event_graphrag.conflict_detection import (
    ConflictDetectionError,
    detect_conflicts,
    detect_rule_based_conflict,
    generate_conflict_candidates,
    group_claims_by_event_and_topic,
)
from claim_aware_event_graphrag.schemas import Claim, Event


def _event(event_id: str = "E001") -> Event:
    return Event(
        event_id=event_id,
        time="2026-03-04",
        type="military",
        summary="A strike near a port facility.",
        actors=["State A", "State B"],
        location="Meridian Port",
    )


def _claim(
    claim_id: str,
    event_id: str = "E001",
    topic: str = "target",
    claimant: str = "Actor A",
    text: str = "Some statement",
    stance: str = "assert",
) -> Claim:
    return Claim(
        claim_id=claim_id,
        event_id=event_id,
        claimant=claimant,
        text=text,
        topic=topic,
        stance=stance,
        source_chunk_id="chunk_001",
    )


def test_group_claims_by_event_and_topic_groups_correctly() -> None:
    claims = [
        _claim("C001", topic="target"),
        _claim("C002", topic="target", claimant="Actor B"),
        _claim("C003", topic="damage"),
    ]

    grouped = group_claims_by_event_and_topic(claims)

    assert ("E001", "target") in grouped
    assert ("E001", "damage") not in grouped


def test_generate_conflict_candidates_requires_different_claimants() -> None:
    claims = [
        _claim("C001", topic="target", claimant="Actor A"),
        _claim("C002", topic="target", claimant="Actor A"),
        _claim("C003", topic="target", claimant="Actor B"),
    ]

    candidates = generate_conflict_candidates(claims)

    assert len(candidates) == 1
    assert len(candidates[0]) == 2


def test_target_conflict_high() -> None:
    event = _event()
    claims = [
        _claim("C001", topic="target", claimant="A", text="The strike hit a military facility."),
        _claim("C002", topic="target", claimant="B", text="The strike hit civilian infrastructure."),
    ]

    conflict = detect_rule_based_conflict(event, claims, 1)

    assert conflict.is_conflict is True
    assert conflict.severity == "high"


def test_economic_impact_conflict_medium() -> None:
    event = _event(event_id="E002")
    claims = [
        _claim("C010", event_id="E002", topic="economic_impact", claimant="A", text="Oil prices would not change."),
        _claim("C011", event_id="E002", topic="economic_impact", claimant="B", text="Prices rose after the strike."),
    ]

    conflict = detect_rule_based_conflict(event, claims, 1)

    assert conflict.is_conflict is True
    assert conflict.severity == "medium"


def test_verification_unverified_not_direct_conflict() -> None:
    event = _event(event_id="E003")
    claims = [
        _claim("C020", event_id="E003", topic="verification", claimant="A", text="This could not be independently verified."),
        _claim("C021", event_id="E003", topic="verification", claimant="B", text="The report remains unverified."),
    ]

    conflict = detect_rule_based_conflict(event, claims, 1)

    assert conflict.is_conflict is False
    assert conflict.severity == "none"


def test_casualty_conflict_high() -> None:
    event = _event(event_id="E004")
    claims = [
        _claim("C030", event_id="E004", topic="casualty", claimant="A", text="No casualties were reported."),
        _claim("C031", event_id="E004", topic="casualty", claimant="B", text="12 casualties and 3 killed were reported."),
    ]

    conflict = detect_rule_based_conflict(event, claims, 1)

    assert conflict.is_conflict is True
    assert conflict.severity == "high"


def test_damage_conflict_detected() -> None:
    event = _event(event_id="E005")
    claims = [
        _claim("C040", event_id="E005", topic="damage", claimant="A", text="There was no damage to the main site."),
        _claim("C041", event_id="E005", topic="damage", claimant="B", text="The main facility was destroyed."),
    ]

    conflict = detect_rule_based_conflict(event, claims, 1)

    assert conflict.is_conflict is True


def test_stance_deny_vs_assert_can_trigger_conflict() -> None:
    event = _event(event_id="E006")
    claims = [
        _claim("C050", event_id="E006", topic="responsibility", claimant="A", text="State X conducted the strike.", stance="assert"),
        _claim("C051", event_id="E006", topic="responsibility", claimant="B", text="State X did not conduct the strike.", stance="deny"),
    ]

    conflict = detect_rule_based_conflict(event, claims, 1)

    assert conflict.is_conflict is True
    assert conflict.severity == "medium"


def test_default_unrelated_text_not_conflict() -> None:
    event = _event(event_id="E007")
    claims = [
        _claim("C060", event_id="E007", topic="other", claimant="A", text="The weather was clear."),
        _claim("C061", event_id="E007", topic="other", claimant="B", text="Ships continued normal operations."),
    ]

    conflict = detect_rule_based_conflict(event, claims, 1)

    assert conflict.is_conflict is False


def test_detect_conflicts_stable_ids() -> None:
    event = _event()
    claims = [
        _claim("C001", topic="target", claimant="A", text="military facility"),
        _claim("C002", topic="target", claimant="B", text="civilian infrastructure"),
    ]

    conflicts = detect_conflicts([event], claims)

    assert conflicts[0].conflict_id == "CF001"


def test_detect_conflicts_missing_event_raises_error() -> None:
    claims = [
        _claim("C001", event_id="E999", topic="target", claimant="A", text="military facility"),
        _claim("C002", event_id="E999", topic="target", claimant="B", text="civilian infrastructure"),
    ]

    with pytest.raises(ConflictDetectionError):
        detect_conflicts([], claims)
