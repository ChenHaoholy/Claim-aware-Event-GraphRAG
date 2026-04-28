from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.jsonl import load_chunks, load_claims, load_events
    from claim_aware_event_graphrag.validation import validate_dataset

    sample_dir = root / "data" / "sample"

    chunks = load_chunks(sample_dir / "chunks.jsonl")
    events = load_events(sample_dir / "events.jsonl")
    claims = load_claims(sample_dir / "claims.jsonl")

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
