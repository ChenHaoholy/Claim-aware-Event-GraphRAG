from __future__ import annotations

import json
from pathlib import Path

from .answer_generation import format_answer_markdown, generate_answer_from_context
from .jsonl import read_jsonl
from .retrieval import format_retrieval_result, retrieve_context


def _normalize_text(value: str) -> str:
    return value.lower().strip()


def _keyword_hit_stats(text: str, expected_keywords: list[str]) -> dict[str, object]:
    normalized_text = _normalize_text(text)
    normalized_keywords = [_normalize_text(keyword) for keyword in expected_keywords]

    matched: list[str] = []
    missed: list[str] = []

    for keyword in normalized_keywords:
        if keyword == "":
            continue
        if keyword in normalized_text:
            matched.append(keyword)
        else:
            missed.append(keyword)

    total_count = len([keyword for keyword in normalized_keywords if keyword != ""])
    hit_count = len(matched)
    hit_rate = 1.0 if total_count == 0 else hit_count / total_count

    return {
        "hit_count": hit_count,
        "total_count": total_count,
        "hit_rate": round(hit_rate, 4),
        "matched_keywords": matched,
        "missed_keywords": missed,
    }


def load_eval_questions(path: str | Path) -> list[dict]:
    return read_jsonl(path)


def evaluate_answer_keywords(answer_markdown: str, expected_keywords: list[str]) -> dict:
    return _keyword_hit_stats(answer_markdown, expected_keywords)


def evaluate_retrieval_context(retrieval_context: dict, eval_question: dict) -> dict:
    events_text = "\n".join(
        json.dumps(event, ensure_ascii=False) for event in retrieval_context.get("events", [])
    )
    claims_text = "\n".join(
        json.dumps(claim, ensure_ascii=False) for claim in retrieval_context.get("claims", [])
    )
    conflicts_text = "\n".join(
        json.dumps(conflict, ensure_ascii=False) for conflict in retrieval_context.get("conflicts", [])
    )

    event_eval = _keyword_hit_stats(events_text, eval_question.get("expected_event_keywords", []))
    claim_eval = _keyword_hit_stats(claims_text, eval_question.get("expected_claim_keywords", []))
    conflict_eval = _keyword_hit_stats(
        conflicts_text,
        eval_question.get("expected_conflict_keywords", []),
    )

    return {
        "event_keyword_eval": event_eval,
        "claim_keyword_eval": claim_eval,
        "conflict_keyword_eval": conflict_eval,
    }


def run_eval_question(
    question: dict,
    chunks: list,
    events: list,
    claims: list,
    conflicts: list,
) -> dict:
    question_text = str(question.get("question", "")).strip()
    retrieval_result = retrieve_context(question_text, chunks, events, claims, conflicts)
    retrieval_context = format_retrieval_result(retrieval_result, chunks, events, claims, conflicts)

    answer = generate_answer_from_context(retrieval_context)
    answer_markdown = format_answer_markdown(answer)

    retrieval_eval = evaluate_retrieval_context(retrieval_context, question)
    answer_eval = evaluate_answer_keywords(
        answer_markdown,
        question.get("expected_answer_keywords", []),
    )

    return {
        "question_id": question.get("question_id"),
        "question": question_text,
        "category": question.get("category"),
        "retrieval_counts": {
            "events": len(retrieval_context.get("events", [])),
            "claims": len(retrieval_context.get("claims", [])),
            "conflicts": len(retrieval_context.get("conflicts", [])),
            "chunks": len(retrieval_context.get("chunks", [])),
        },
        "event_keyword_eval": retrieval_eval["event_keyword_eval"],
        "claim_keyword_eval": retrieval_eval["claim_keyword_eval"],
        "conflict_keyword_eval": retrieval_eval["conflict_keyword_eval"],
        "answer_keyword_eval": answer_eval,
        "answer_markdown": answer_markdown,
    }


def run_eval_questions(
    questions: list[dict],
    chunks: list,
    events: list,
    claims: list,
    conflicts: list,
) -> list[dict]:
    results: list[dict] = []
    for question in questions:
        results.append(run_eval_question(question, chunks, events, claims, conflicts))
    return results
