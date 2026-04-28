import pytest
from pydantic import ValidationError

from claim_aware_event_graphrag.schemas import Chunk, Claim, Event


def test_valid_models_can_be_created() -> None:
    chunk = Chunk(chunk_id="c1", doc_id="d1", source=None, date=None, text="evidence")
    event = Event(
        event_id="e1",
        time=None,
        type="military",
        summary="summary",
        actors=["Actor A"],
        location=None,
    )
    claim = Claim(
        claim_id="cl1",
        event_id="e1",
        claimant="Spokesperson",
        text="claim text",
        topic="target",
        stance="assert",
        source_chunk_id="c1",
    )

    assert chunk.chunk_id == "c1"
    assert event.type == "military"
    assert claim.stance == "assert"


def test_empty_text_raises_error() -> None:
    with pytest.raises(ValidationError):
        Chunk(chunk_id="c1", doc_id="d1", source=None, date=None, text="")


def test_invalid_event_type_raises_error() -> None:
    with pytest.raises(ValidationError):
        Event(
            event_id="e1",
            time=None,
            type="cyber",
            summary="summary",
            actors=["Actor A"],
            location=None,
        )


def test_invalid_claim_topic_raises_error() -> None:
    with pytest.raises(ValidationError):
        Claim(
            claim_id="cl1",
            event_id="e1",
            claimant="Spokesperson",
            text="claim text",
            topic="narrative",
            stance="assert",
            source_chunk_id="c1",
        )


def test_invalid_claim_stance_raises_error() -> None:
    with pytest.raises(ValidationError):
        Claim(
            claim_id="cl1",
            event_id="e1",
            claimant="Spokesperson",
            text="claim text",
            topic="target",
            stance="support",
            source_chunk_id="c1",
        )


def test_actors_with_empty_string_raises_error() -> None:
    with pytest.raises(ValidationError):
        Event(
            event_id="e1",
            time=None,
            type="military",
            summary="summary",
            actors=["Actor A", ""],
            location=None,
        )
