import pytest

from claim_aware_event_graphrag.event_merge import (
    EventMergeError,
    actor_overlap,
    canonicalize_claims,
    cluster_temp_events,
    events_maybe_same,
    make_canonical_event,
    merge_temp_extraction,
    normalize_actor,
    normalize_text,
    simple_token_similarity,
)
from claim_aware_event_graphrag.schemas import TempClaim, TempEvent


def _temp_event(
    temp_event_id: str,
    chunk_id: str,
    event_type: str = "military",
    time: str | None = "2026-03-04",
    location: str | None = "Meridian Port",
    summary: str = "Strike hit port facility",
    actors: list[str] | None = None,
) -> TempEvent:
    return TempEvent(
        temp_event_id=temp_event_id,
        chunk_id=chunk_id,
        time=time,
        type=event_type,
        summary=summary,
        actors=actors or ["United States"],
        location=location,
    )


def _temp_claim(temp_claim_id: str, temp_event_id: str, chunk_id: str) -> TempClaim:
    return TempClaim(
        temp_claim_id=temp_claim_id,
        temp_event_id=temp_event_id,
        chunk_id=chunk_id,
        claimant="Spokesperson",
        text="Claim text",
        topic="target",
        stance="assert",
        source_chunk_id=chunk_id,
    )


def test_normalize_text_handles_none_case_and_spaces() -> None:
    assert normalize_text(None) == ""
    assert normalize_text("  HeLLo   WORLD ") == "hello world"


def test_normalize_actor_maps_us_variants() -> None:
    assert normalize_actor("us") == "united states"
    assert normalize_actor("U.S.") == "united states"
    assert normalize_actor("USA") == "united states"


def test_actor_overlap_works() -> None:
    score = actor_overlap(["US", "Israel"], ["U.S.", "israel"])
    assert score == 1.0


def test_simple_token_similarity_works() -> None:
    score = simple_token_similarity("Strike at port.", "Port strike reported")
    assert score > 0.3


def test_events_maybe_same_true_for_obviously_same_events() -> None:
    a = _temp_event("e1", "chunk_1")
    b = _temp_event("e2", "chunk_2", summary="Strike hit Meridian Port facility")

    same, score, _ = events_maybe_same(a, b)

    assert same is True
    assert score >= 0.60


def test_events_maybe_same_does_not_merge_military_and_economic() -> None:
    a = _temp_event("e1", "chunk_1", event_type="military")
    b = _temp_event("e2", "chunk_2", event_type="economic", summary="Market reacted to strike")

    same, _, _ = events_maybe_same(a, b)

    assert same is False


def test_events_maybe_same_false_for_different_time_and_location() -> None:
    a = _temp_event("e1", "chunk_1", time="2026-03-04", location="Meridian Port")
    b = _temp_event("e2", "chunk_2", time="2026-03-05", location="Northern Gulf")

    same, _, _ = events_maybe_same(a, b)

    assert same is False


def test_cluster_temp_events_groups_similar_events() -> None:
    events = [
        _temp_event("e1", "chunk_1"),
        _temp_event("e2", "chunk_2", summary="Strike hit Meridian Port facility"),
        _temp_event("e3", "chunk_3", event_type="economic", summary="Oil prices rose"),
    ]

    clusters = cluster_temp_events(events)

    sizes = sorted(len(cluster) for cluster in clusters)
    assert sizes == [1, 2]


def test_make_canonical_event_generates_e001_id() -> None:
    cluster = [
        _temp_event("e1", "chunk_1", summary="Short summary"),
        _temp_event("e2", "chunk_2", summary="A longer and more detailed summary"),
    ]

    event = make_canonical_event(cluster, event_index=1)

    assert event.event_id == "E001"
    assert event.summary == "A longer and more detailed summary"


def test_canonicalize_claims_maps_temp_claim_to_claim() -> None:
    claims = [_temp_claim("c1", "chunk_1_e1", "chunk_1")]
    mapping = {"chunk_1_e1": "E001"}

    canonical = canonicalize_claims(claims, mapping)

    assert canonical[0].claim_id == "C001"
    assert canonical[0].event_id == "E001"


def test_canonicalize_claims_raises_for_missing_mapping() -> None:
    claims = [_temp_claim("c1", "chunk_1_e_missing", "chunk_1")]

    with pytest.raises(EventMergeError):
        canonicalize_claims(claims, {})


def test_merge_temp_extraction_returns_events_claims_mapping() -> None:
    temp_events = [
        _temp_event("chunk_1_e1", "chunk_1"),
        _temp_event("chunk_2_e1", "chunk_2", summary="Strike hit Meridian Port facility"),
        _temp_event("chunk_3_e1", "chunk_3", event_type="economic", summary="Oil prices rose"),
    ]
    temp_claims = [
        _temp_claim("chunk_1_c1", "chunk_1_e1", "chunk_1"),
        _temp_claim("chunk_2_c1", "chunk_2_e1", "chunk_2"),
        _temp_claim("chunk_3_c1", "chunk_3_e1", "chunk_3"),
    ]

    events, claims, mapping = merge_temp_extraction(temp_events, temp_claims)

    assert len(events) == 2
    assert len(claims) == 3
    assert len(mapping) == 3
    event_ids = {event.event_id for event in events}
    assert all(claim.event_id in event_ids for claim in claims)
