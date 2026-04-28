from __future__ import annotations

from pathlib import Path
import sys


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.evaluation import load_eval_questions, run_eval_questions
    from claim_aware_event_graphrag.jsonl import (
        load_chunks,
        load_claims,
        load_conflicts,
        load_events,
        write_jsonl,
    )

    questions_path = root / "data" / "eval" / "questions.jsonl"
    chunks_path = root / "data" / "sample" / "chunks.jsonl"
    events_path = root / "data" / "processed" / "events.jsonl"
    claims_path = root / "data" / "processed" / "claims.jsonl"
    conflicts_path = root / "data" / "processed" / "conflicts.jsonl"

    if not (events_path.exists() and claims_path.exists() and conflicts_path.exists()):
        print("Missing processed outputs. Please run: python scripts/run_mvp_sample.py")
        return 1

    questions = load_eval_questions(questions_path)
    chunks = load_chunks(chunks_path)
    events = load_events(events_path)
    claims = load_claims(claims_path)
    conflicts = load_conflicts(conflicts_path)

    results = run_eval_questions(questions, chunks, events, claims, conflicts)

    out_path = root / "data" / "eval" / "results.jsonl"
    write_jsonl(out_path, results)

    event_rates: list[float] = []
    claim_rates: list[float] = []
    conflict_rates: list[float] = []
    answer_rates: list[float] = []

    for result in results:
        event_rate = float(result["event_keyword_eval"]["hit_rate"])
        claim_rate = float(result["claim_keyword_eval"]["hit_rate"])
        conflict_rate = float(result["conflict_keyword_eval"]["hit_rate"])
        answer_rate = float(result["answer_keyword_eval"]["hit_rate"])

        event_rates.append(event_rate)
        claim_rates.append(claim_rate)
        conflict_rates.append(conflict_rate)
        answer_rates.append(answer_rate)

        print(
            f"{result['question_id']} [{result['category']}] "
            f"event_hit_rate={event_rate:.2f} "
            f"claim_hit_rate={claim_rate:.2f} "
            f"conflict_hit_rate={conflict_rate:.2f} "
            f"answer_hit_rate={answer_rate:.2f}"
        )

    print("\n=== Overall average hit rates ===")
    print(f"event_hit_rate_avg={_average(event_rates):.2f}")
    print(f"claim_hit_rate_avg={_average(claim_rates):.2f}")
    print(f"conflict_hit_rate_avg={_average(conflict_rates):.2f}")
    print(f"answer_hit_rate_avg={_average(answer_rates):.2f}")
    print(f"results_path: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
