from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.jsonl import load_chunks, load_claims, load_events
    from claim_aware_event_graphrag.validation import validate_dataset

    chunks_path = root / "data" / "sample" / "chunks.jsonl"
    events_path = root / "data" / "processed" / "events.jsonl"
    claims_path = root / "data" / "processed" / "claims.jsonl"

    if not events_path.exists() or not claims_path.exists():
        print("Missing processed canonical files. Please run: python scripts/merge_sample.py")
        return 1

    chunks = load_chunks(chunks_path)
    events = load_events(events_path)
    claims = load_claims(claims_path)

    errors = validate_dataset(chunks, events, claims)

    print(f"chunks: {len(chunks)}")
    print(f"events: {len(events)}")
    print(f"claims: {len(claims)}")

    if errors:
        print("validation: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("validation: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
