from claim_aware_event_graphrag.schemas import Claim, Conflict, Event
from claim_aware_event_graphrag.validation import validate_conflicts


def _event(event_id: str = "E001") -> Event:
    return Event(
        event_id=event_id,
        time=None,
        type="military",
        summary="summary",
        actors=["A"],
        location=None,
    )


def _claim(claim_id: str, event_id: str = "E001", topic: str = "target") -> Claim:
    return Claim(
        claim_id=claim_id,
        event_id=event_id,
        claimant="A",
        text="text",
        topic=topic,
        stance="assert",
        source_chunk_id="chunk_001",
    )


def _conflict(
    conflict_id: str = "CF001",
    event_id: str = "E001",
    claim_ids: list[str] | None = None,
    topic: str = "target",
    is_conflict: bool = True,
    severity: str = "high",
    explanation: str = "explanation",
) -> Conflict:
    return Conflict(
        conflict_id=conflict_id,
        event_id=event_id,
        claim_ids=claim_ids or ["C001", "C002"],
        topic=topic,
        is_conflict=is_conflict,
        severity=severity,
        explanation=explanation,
    )


def test_valid_conflicts_validation_passes() -> None:
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict()]

    errors = validate_conflicts(events, claims, conflicts)

    assert errors == []


def test_duplicate_conflict_id_detected() -> None:
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict("CF001"), _conflict("CF001")]

    errors = validate_conflicts(events, claims, conflicts)

    assert "Duplicate conflict_id: CF001" in errors


def test_missing_event_id_detected() -> None:
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict(event_id="E999")]

    errors = validate_conflicts(events, claims, conflicts)

    assert "Conflict CF001 references missing event_id E999" in errors


def test_missing_claim_id_detected() -> None:
    events = [_event()]
    claims = [_claim("C001")]
    conflicts = [_conflict(claim_ids=["C001", "C999"])]

    errors = validate_conflicts(events, claims, conflicts)

    assert "Conflict CF001 references missing claim_id C999" in errors


def test_conflict_claims_multiple_events_detected() -> None:
    events = [_event("E001"), _event("E002")]
    claims = [_claim("C001", "E001"), _claim("C002", "E002")]
    conflicts = [_conflict(event_id="E001", claim_ids=["C001", "C002"])]

    errors = validate_conflicts(events, claims, conflicts)

    assert any("multiple event_ids" in err for err in errors)


def test_is_conflict_false_with_non_none_severity_detected() -> None:
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict(is_conflict=False, severity="low")]

    errors = validate_conflicts(events, claims, conflicts)

    assert "Conflict CF001 has is_conflict=false but severity=low" in errors


def test_is_conflict_true_with_none_severity_detected() -> None:
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict(is_conflict=True, severity="none")]

    errors = validate_conflicts(events, claims, conflicts)

    assert "Conflict CF001 has is_conflict=true but severity=none" in errors
