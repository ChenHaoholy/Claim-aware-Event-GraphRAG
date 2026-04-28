from pathlib import Path

from claim_aware_event_graphrag.evaluation import (
    evaluate_answer_keywords,
    evaluate_retrieval_context,
    load_eval_questions,
    run_eval_question,
    run_eval_questions,
)
from claim_aware_event_graphrag.jsonl import read_jsonl, write_jsonl
from claim_aware_event_graphrag.schemas import Chunk, Claim, Conflict, Event


def _sample_data() -> tuple[list[Chunk], list[Event], list[Claim], list[Conflict]]:
    chunks = [
        Chunk(
            chunk_id="chunk_001",
            doc_id="doc_1",
            source="src",
            date="2026-03-04",
            text="Strike near Meridian Port and reports of facility damage.",
        )
    ]

    events = [
        Event(
            event_id="E001",
            time="2026-03-04",
            type="military",
            summary="A strike happened near Meridian Port.",
            actors=["State A", "State B"],
            location="Meridian Port",
        )
    ]

    claims = [
        Claim(
            claim_id="C001",
            event_id="E001",
            claimant="State A",
            text="The strike targeted a military facility.",
            topic="target",
            stance="assert",
            source_chunk_id="chunk_001",
        ),
        Claim(
            claim_id="C002",
            event_id="E001",
            claimant="State B",
            text="The strike hit civilian infrastructure.",
            topic="target",
            stance="deny",
            source_chunk_id="chunk_001",
        ),
    ]

    conflicts = [
        Conflict(
            conflict_id="CF001",
            event_id="E001",
            claim_ids=["C001", "C002"],
            topic="target",
            is_conflict=True,
            severity="high",
            explanation="Target claims conflict.",
        )
    ]

    return chunks, events, claims, conflicts


def test_load_eval_questions() -> None:
    root = Path(__file__).resolve().parents[1]
    questions = load_eval_questions(root / "data" / "eval" / "questions.jsonl")

    assert len(questions) >= 6
    assert {"question_id", "question", "category"}.issubset(set(questions[0].keys()))


def test_evaluate_answer_keywords_counts_hits() -> None:
    answer = "military facility and civilian infrastructure are in conflict"
    result = evaluate_answer_keywords(answer, ["military", "civilian", "conflict", "missing"])

    assert result["hit_count"] == 3
    assert result["total_count"] == 4
    assert result["hit_rate"] == 0.75


def test_evaluate_retrieval_context_works() -> None:
    retrieval_context = {
        "events": [{"summary": "Strike near Meridian Port", "type": "military"}],
        "claims": [{"text": "targeted a military facility"}],
        "conflicts": [{"topic": "target", "explanation": "claims conflict"}],
    }
    eval_question = {
        "expected_event_keywords": ["Meridian Port"],
        "expected_claim_keywords": ["military facility"],
        "expected_conflict_keywords": ["conflict"],
    }

    result = evaluate_retrieval_context(retrieval_context, eval_question)

    assert result["event_keyword_eval"]["hit_count"] == 1
    assert result["claim_keyword_eval"]["hit_count"] == 1
    assert result["conflict_keyword_eval"]["hit_count"] == 1


def test_run_eval_question_returns_expected_fields() -> None:
    chunks, events, claims, conflicts = _sample_data()
    eval_question = {
        "question_id": "Q001",
        "question": "What claims conflict about the target?",
        "category": "conflict",
        "expected_event_keywords": ["strike"],
        "expected_claim_keywords": ["military facility"],
        "expected_conflict_keywords": ["target"],
        "expected_answer_keywords": ["conflict"],
    }

    result = run_eval_question(eval_question, chunks, events, claims, conflicts)

    assert result["question_id"] == "Q001"
    assert "event_keyword_eval" in result
    assert "claim_keyword_eval" in result
    assert "conflict_keyword_eval" in result
    assert "answer_keyword_eval" in result
    assert "answer_markdown" in result


def test_run_eval_questions_handles_multiple_questions() -> None:
    chunks, events, claims, conflicts = _sample_data()
    questions = [
        {
            "question_id": "Q001",
            "question": "What claims conflict about the target?",
            "category": "conflict",
            "expected_event_keywords": ["strike"],
            "expected_claim_keywords": ["military facility"],
            "expected_conflict_keywords": ["target"],
            "expected_answer_keywords": ["conflict"],
        },
        {
            "question_id": "Q002",
            "question": "What happened near Meridian Port?",
            "category": "location",
            "expected_event_keywords": ["Meridian Port"],
            "expected_claim_keywords": [],
            "expected_conflict_keywords": [],
            "expected_answer_keywords": ["Meridian Port"],
        },
    ]

    results = run_eval_questions(questions, chunks, events, claims, conflicts)

    assert len(results) == 2
    assert results[0]["question_id"] == "Q001"
    assert results[1]["question_id"] == "Q002"


def test_empty_expected_keywords_should_not_error() -> None:
    result = evaluate_answer_keywords("any text", [])
    assert result["total_count"] == 0
    assert result["hit_count"] == 0
    assert result["hit_rate"] == 1.0


def test_results_can_be_written_as_jsonl(tmp_path: Path) -> None:
    rows = [
        {
            "question_id": "Q001",
            "category": "conflict",
            "event_keyword_eval": {"hit_rate": 1.0},
        }
    ]

    out_path = tmp_path / "results.jsonl"
    write_jsonl(out_path, rows)
    loaded = read_jsonl(out_path)

    assert loaded == rows
