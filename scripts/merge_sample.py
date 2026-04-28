from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.event_merge import merge_temp_extraction
    from claim_aware_event_graphrag.jsonl import (
        load_temp_claims,
        load_temp_events,
        write_jsonl,
    )

    processed_dir = root / "data" / "processed"
    temp_events_path = processed_dir / "temp_events.jsonl"
    temp_claims_path = processed_dir / "temp_claims.jsonl"

    if not temp_events_path.exists() or not temp_claims_path.exists():
        print("Missing temp extraction files. Please run: python scripts/extract_sample.py")
        return 1

    temp_events = load_temp_events(temp_events_path)
    temp_claims = load_temp_claims(temp_claims_path)

    events, claims, mapping = merge_temp_extraction(temp_events, temp_claims)

    events_path = processed_dir / "events.jsonl"
    claims_path = processed_dir / "claims.jsonl"
    mapping_path = processed_dir / "temp_event_mapping.jsonl"

    write_jsonl(events_path, [event.model_dump(mode="json") for event in events])
    write_jsonl(claims_path, [claim.model_dump(mode="json") for claim in claims])
    write_jsonl(
        mapping_path,
        [
            {"temp_event_id": temp_event_id, "event_id": event_id}
            for temp_event_id, event_id in sorted(mapping.items())
        ],
    )

    print(f"temp_events: {len(temp_events)}")
    print(f"temp_claims: {len(temp_claims)}")
    print(f"canonical_events: {len(events)}")
    print(f"canonical_claims: {len(claims)}")
    print(f"events_path: {events_path}")
    print(f"claims_path: {claims_path}")
    print(f"mapping_path: {mapping_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
