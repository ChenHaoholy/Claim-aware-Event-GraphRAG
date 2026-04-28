import pytest

from claim_aware_event_graphrag.extraction import ExtractionError, extract_from_chunk
from claim_aware_event_graphrag.llm import MockLLMClient
from claim_aware_event_graphrag.schemas import Chunk


class StaticLLMClient:
    def __init__(self, output: str) -> None:
        self.output = output

    def complete(self, prompt: str) -> str:
        return self.output


class BadRefLLMClient:
    def complete(self, prompt: str) -> str:
        return (
            '{"temp_events": [{"temp_event_id": "e1", "time": null, "type": "other", '
            '"summary": "event", "actors": [], "location": null}], '
            '"temp_claims": [{"temp_claim_id": "c1", "temp_event_id": "e999", '
            '"claimant": "A", "text": "text", "topic": "other", "stance": "report"}]}'
        )


def test_extract_from_chunk_with_mock_llm_returns_temp_objects() -> None:
    chunk = Chunk(
        chunk_id="chunk_001",
        doc_id="d1",
        source="test",
        date="2026-01-01",
        text="The strike hit a military facility, while others said it was civilian infrastructure.",
    )

    result = extract_from_chunk(chunk, MockLLMClient())

    assert len(result.temp_events) == 1
    assert len(result.temp_claims) == 2


def test_temp_event_id_gets_chunk_prefix() -> None:
    chunk = Chunk(chunk_id="chunk_123", doc_id="d1", source=None, date=None, text="oil prices moved")

    result = extract_from_chunk(chunk, MockLLMClient())

    assert result.temp_events[0].temp_event_id.startswith("chunk_123_")


def test_temp_claim_id_gets_chunk_prefix() -> None:
    chunk = Chunk(chunk_id="chunk_123", doc_id="d1", source=None, date=None, text="oil prices moved")

    result = extract_from_chunk(chunk, MockLLMClient())

    assert result.temp_claims[0].temp_claim_id.startswith("chunk_123_")


def test_source_chunk_id_is_auto_filled() -> None:
    chunk = Chunk(chunk_id="chunk_456", doc_id="d1", source=None, date=None, text="oil prices moved")

    result = extract_from_chunk(chunk, MockLLMClient())

    assert result.temp_claims[0].source_chunk_id == "chunk_456"


def test_missing_temp_event_reference_raises_error() -> None:
    chunk = Chunk(chunk_id="chunk_789", doc_id="d1", source=None, date=None, text="any")

    with pytest.raises(ExtractionError):
        extract_from_chunk(chunk, BadRefLLMClient())


def test_invalid_json_raises_error() -> None:
    chunk = Chunk(chunk_id="chunk_bad", doc_id="d1", source=None, date=None, text="any")

    with pytest.raises(ExtractionError):
        extract_from_chunk(chunk, StaticLLMClient("not-json"))


def test_empty_result_is_valid() -> None:
    chunk = Chunk(chunk_id="chunk_empty", doc_id="d1", source=None, date=None, text="no signal")

    result = extract_from_chunk(chunk, MockLLMClient())

    assert result.temp_events == []
    assert result.temp_claims == []
