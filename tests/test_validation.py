from pathlib import Path

from claim_aware_event_graphrag.jsonl import load_chunks, load_claims, load_events
from claim_aware_event_graphrag.schemas import Chunk, Claim, Event
from claim_aware_event_graphrag.validation import validate_dataset


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample"


def test_sample_data_validation_passes() -> None:
    chunks = load_chunks(SAMPLE_DIR / "chunks.jsonl")
    events = load_events(SAMPLE_DIR / "events.jsonl")
    claims = load_claims(SAMPLE_DIR / "claims.jsonl")

    errors = validate_dataset(chunks, events, claims)

    assert errors == []


def test_duplicate_chunk_id_detected() -> None:
    chunks = [
        Chunk(chunk_id="c1", doc_id="d1", source=None, date=None, text="x"),
        Chunk(chunk_id="c1", doc_id="d2", source=None, date=None, text="y"),
    ]
    events: list[Event] = []
    claims: list[Claim] = []

    errors = validate_dataset(chunks, events, claims)

    assert "Duplicate chunk_id: c1" in errors


def test_missing_event_reference_detected() -> None:
    chunks = [Chunk(chunk_id="c1", doc_id="d1", source=None, date=None, text="x")]
    events = [
        Event(
            event_id="e1",
            time=None,
            type="military",
            summary="summary",
            actors=[],
            location=None,
        )
    ]
    claims = [
        Claim(
            claim_id="cl1",
            event_id="e999",
            claimant="A",
            text="t",
            topic="target",
            stance="assert",
            source_chunk_id="c1",
        )
    ]

    errors = validate_dataset(chunks, events, claims)

    assert "Claim cl1 references missing event_id e999" in errors


def test_missing_chunk_reference_detected() -> None:
    chunks = [Chunk(chunk_id="c1", doc_id="d1", source=None, date=None, text="x")]
    events = [
        Event(
            event_id="e1",
            time=None,
            type="military",
            summary="summary",
            actors=[],
            location=None,
        )
    ]
    claims = [
        Claim(
            claim_id="cl1",
            event_id="e1",
            claimant="A",
            text="t",
            topic="target",
            stance="assert",
            source_chunk_id="c999",
        )
    ]

    errors = validate_dataset(chunks, events, claims)

    assert "Claim cl1 references missing source_chunk_id c999" in errors


def test_duplicate_claim_id_detected() -> None:
    chunks = [Chunk(chunk_id="c1", doc_id="d1", source=None, date=None, text="x")]
    events = [
        Event(
            event_id="e1",
            time=None,
            type="military",
            summary="summary",
            actors=[],
            location=None,
        )
    ]
    claims = [
        Claim(
            claim_id="cl1",
            event_id="e1",
            claimant="A",
            text="t",
            topic="target",
            stance="assert",
            source_chunk_id="c1",
        ),
        Claim(
            claim_id="cl1",
            event_id="e1",
            claimant="B",
            text="t2",
            topic="response",
            stance="report",
            source_chunk_id="c1",
        ),
    ]

    errors = validate_dataset(chunks, events, claims)

    assert "Duplicate claim_id: cl1" in errors


def test_duplicate_event_id_detected() -> None:
    chunks: list[Chunk] = []
    events = [
        Event(event_id="e1", time=None, type="military", summary="s1", actors=[], location=None),
        Event(event_id="e1", time=None, type="diplomatic", summary="s2", actors=[], location=None),
    ]
    claims: list[Claim] = []

    errors = validate_dataset(chunks, events, claims)

    assert "Duplicate event_id: e1" in errors
