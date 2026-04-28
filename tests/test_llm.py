from claim_aware_event_graphrag.extraction import extract_from_chunk
from claim_aware_event_graphrag.llm import MockLLMClient, get_llm_client
from claim_aware_event_graphrag.schemas import Chunk


class StaticLLMClient:
    def __init__(self, output: str) -> None:
        self.output = output

    def complete(self, prompt: str) -> str:
        return self.output


def test_get_llm_client_defaults_to_mock() -> None:
    client = get_llm_client()
    assert isinstance(client, MockLLMClient)


def test_get_llm_client_deepseek_without_api_key_raises(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    try:
        get_llm_client("deepseek")
        assert False, "expected ValueError for missing DEEPSEEK_API_KEY"
    except ValueError as exc:
        assert "DEEPSEEK_API_KEY" in str(exc)


def test_get_llm_client_unknown_provider_raises() -> None:
    try:
        get_llm_client("unknown")
        assert False, "expected ValueError for unknown provider"
    except ValueError as exc:
        assert "Unknown llm provider" in str(exc)


def test_extract_from_chunk_accepts_json_fence() -> None:
    chunk = Chunk(chunk_id="chunk_001", doc_id="d1", source=None, date=None, text="text")
    llm_output = """
```json
{
  "temp_events": [
    {
      "temp_event_id": "e1",
      "time": null,
      "type": "other",
      "summary": "fenced",
      "actors": ["a"],
      "location": null
    }
  ],
  "temp_claims": [
    {
      "temp_claim_id": "c1",
      "temp_event_id": "e1",
      "claimant": "a",
      "text": "t",
      "topic": "other",
      "stance": "report"
    }
  ]
}
```
"""

    result = extract_from_chunk(chunk, StaticLLMClient(llm_output))
    assert len(result.temp_events) == 1
    assert len(result.temp_claims) == 1


def test_extract_from_chunk_accepts_generic_fence() -> None:
    chunk = Chunk(chunk_id="chunk_002", doc_id="d1", source=None, date=None, text="text")
    llm_output = """
```
{"temp_events": [], "temp_claims": []}
```
"""
    result = extract_from_chunk(chunk, StaticLLMClient(llm_output))
    assert result.temp_events == []
    assert result.temp_claims == []
