from claim_aware_event_graphrag.schemas import Chunk, TempClaim, TempEvent
from claim_aware_event_graphrag.validation import validate_temp_extraction


def _chunk(chunk_id: str) -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id=f"doc_{chunk_id}", source=None, date=None, text="text")


def test_valid_temp_extraction_passes() -> None:
    chunks = [_chunk("chunk_1")]
    temp_events = [
        TempEvent(
            temp_event_id="chunk_1_e1",
            chunk_id="chunk_1",
            time=None,
            type="military",
            summary="summary",
            actors=["Actor A"],
            location=None,
        )
    ]
    temp_claims = [
        TempClaim(
            temp_claim_id="chunk_1_c1",
            temp_event_id="chunk_1_e1",
            chunk_id="chunk_1",
            claimant="Actor A",
            text="claim",
            topic="target",
            stance="assert",
            source_chunk_id="chunk_1",
        )
    ]

    errors = validate_temp_extraction(chunks, temp_events, temp_claims)
    assert errors == []


def test_duplicate_temp_event_id_detected() -> None:
    chunks = [_chunk("chunk_1")]
    temp_events = [
        TempEvent(temp_event_id="chunk_1_e1", chunk_id="chunk_1", time=None, type="other", summary="a", actors=[], location=None),
        TempEvent(temp_event_id="chunk_1_e1", chunk_id="chunk_1", time=None, type="other", summary="b", actors=[], location=None),
    ]

    errors = validate_temp_extraction(chunks, temp_events, [])
    assert "Duplicate temp_event_id: chunk_1_e1" in errors


def test_duplicate_temp_claim_id_detected() -> None:
    chunks = [_chunk("chunk_1")]
    temp_events = [
        TempEvent(temp_event_id="chunk_1_e1", chunk_id="chunk_1", time=None, type="other", summary="a", actors=[], location=None)
    ]
    temp_claims = [
        TempClaim(temp_claim_id="chunk_1_c1", temp_event_id="chunk_1_e1", chunk_id="chunk_1", claimant="A", text="x", topic="other", stance="report", source_chunk_id="chunk_1"),
        TempClaim(temp_claim_id="chunk_1_c1", temp_event_id="chunk_1_e1", chunk_id="chunk_1", claimant="B", text="y", topic="other", stance="report", source_chunk_id="chunk_1"),
    ]

    errors = validate_temp_extraction(chunks, temp_events, temp_claims)
    assert "Duplicate temp_claim_id: chunk_1_c1" in errors


def test_missing_temp_event_reference_detected() -> None:
    chunks = [_chunk("chunk_1")]
    temp_events = []
    temp_claims = [
        TempClaim(temp_claim_id="chunk_1_c1", temp_event_id="chunk_1_e9", chunk_id="chunk_1", claimant="A", text="x", topic="other", stance="report", source_chunk_id="chunk_1")
    ]

    errors = validate_temp_extraction(chunks, temp_events, temp_claims)
    assert "TempClaim chunk_1_c1 references missing temp_event_id chunk_1_e9" in errors


def test_claim_event_chunk_mismatch_detected() -> None:
    chunks = [_chunk("chunk_1"), _chunk("chunk_2")]
    temp_events = [
        TempEvent(temp_event_id="chunk_1_e1", chunk_id="chunk_1", time=None, type="other", summary="a", actors=[], location=None)
    ]
    temp_claims = [
        TempClaim(temp_claim_id="chunk_2_c1", temp_event_id="chunk_1_e1", chunk_id="chunk_2", claimant="A", text="x", topic="other", stance="report", source_chunk_id="chunk_2")
    ]

    errors = validate_temp_extraction(chunks, temp_events, temp_claims)
    assert (
        "TempClaim chunk_2_c1 chunk_id chunk_2 does not match TempEvent chunk_1_e1 chunk_id chunk_1"
        in errors
    )
