from claim_aware_event_graphrag.answer_generation import (
    format_answer_markdown,
    generate_answer_from_context,
)


def _retrieval_context() -> dict:
    return {
        "question": "What claims conflict about the target?",
        "events": [
            {
                "event_id": "E001",
                "time": "2026-03-04",
                "type": "military",
                "summary": "A strike happened near Isfahan.",
                "actors": ["Iran", "Israel"],
                "location": "Isfahan",
            }
        ],
        "claims": [
            {
                "claim_id": "C001",
                "event_id": "E001",
                "claimant": "State A",
                "text": "The strike targeted a military facility.",
                "topic": "target",
                "stance": "assert",
                "source_chunk_id": "chunk_001",
            },
            {
                "claim_id": "C002",
                "event_id": "E001",
                "claimant": "State B",
                "text": "The strike hit civilian infrastructure.",
                "topic": "target",
                "stance": "deny",
                "source_chunk_id": "chunk_001",
            },
        ],
        "chunks": [
            {
                "chunk_id": "chunk_001",
                "doc_id": "d1",
                "source": "Newswire",
                "date": "2026-03-04",
                "text": "Reported strike details from local sources.",
            }
        ],
        "conflicts": [
            {
                "conflict_id": "CF001",
                "event_id": "E001",
                "claim_ids": ["C001", "C002"],
                "topic": "target",
                "is_conflict": True,
                "severity": "high",
                "explanation": "Conflicting target claims.",
            }
        ],
        "debug_info": {"query_tokens": ["claims", "conflict", "target"]},
    }


def test_generate_answer_from_context_returns_answer_result() -> None:
    answer = generate_answer_from_context(_retrieval_context())

    assert answer.question == "What claims conflict about the target?"
    assert answer.conclusion
    assert len(answer.key_events) == 1
    assert "State A" in answer.claims_by_actor
    assert len(answer.conflicts_and_uncertainty) == 1
    assert len(answer.evidence) == 1
    assert len(answer.limitations) > 0


def test_format_answer_markdown_contains_required_sections() -> None:
    answer = generate_answer_from_context(_retrieval_context())
    markdown = format_answer_markdown(answer)

    assert "## Conclusion" in markdown
    assert "## Key Events" in markdown
    assert "## Claims by Actor" in markdown
    assert "## Conflicts and Uncertainty" in markdown
    assert "## Evidence" in markdown
    assert "## Limitations" in markdown


def test_generate_answer_handles_empty_context() -> None:
    empty_context = {
        "question": "What happened?",
        "events": [],
        "claims": [],
        "chunks": [],
        "conflicts": [],
        "debug_info": {},
    }
    answer = generate_answer_from_context(empty_context)

    assert answer.conclusion
    assert answer.key_events == []
    assert answer.claims_by_actor == {}
    assert answer.conflicts_and_uncertainty == []
    assert answer.evidence == []
