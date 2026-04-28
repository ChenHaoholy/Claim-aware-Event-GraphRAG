from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.conflict_detection import detect_conflicts
    from claim_aware_event_graphrag.jsonl import (
        load_claims,
        load_chunks,
        load_events,
        write_jsonl,
    )
    from claim_aware_event_graphrag.validation import validate_conflicts

    chunks_path = root / "data" / "sample" / "chunks.jsonl"
    events_path = root / "data" / "processed" / "events.jsonl"
    claims_path = root / "data" / "processed" / "claims.jsonl"

    if not events_path.exists() or not claims_path.exists():
        print(
            "Missing processed events/claims. Please run: python scripts/extract_sample.py and python scripts/merge_sample.py"
        )
        return 1

    _ = load_chunks(chunks_path)
    events = load_events(events_path)
    claims = load_claims(claims_path)

    conflicts = detect_conflicts(events, claims)

    out_path = root / "data" / "processed" / "conflicts.jsonl"
    write_jsonl(out_path, [conflict.model_dump(mode="json") for conflict in conflicts])

    errors = validate_conflicts(events, claims, conflicts)

    print(f"events: {len(events)}")
    print(f"claims: {len(claims)}")
    print(f"conflict_candidates: {len(conflicts)}")
    print(f"true_conflicts: {sum(1 for c in conflicts if c.is_conflict)}")
    print(f"output_path: {out_path}")

    if errors:
        print("validation: FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("validation: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
