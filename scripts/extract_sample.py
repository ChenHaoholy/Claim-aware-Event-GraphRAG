from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.extraction import extract_from_chunks
    from claim_aware_event_graphrag.jsonl import load_chunks, write_jsonl
    from claim_aware_event_graphrag.llm import MockLLMClient

    sample_chunks_path = root / "data" / "sample" / "chunks.jsonl"
    out_dir = root / "data" / "processed"
    temp_events_path = out_dir / "temp_events.jsonl"
    temp_claims_path = out_dir / "temp_claims.jsonl"

    chunks = load_chunks(sample_chunks_path)
    llm_client = MockLLMClient()

    temp_events, temp_claims = extract_from_chunks(chunks, llm_client)

    write_jsonl(temp_events_path, [event.model_dump(mode="json") for event in temp_events])
    write_jsonl(temp_claims_path, [claim.model_dump(mode="json") for claim in temp_claims])

    print(f"chunks: {len(chunks)}")
    print(f"temp_events: {len(temp_events)}")
    print(f"temp_claims: {len(temp_claims)}")
    print(f"temp_events_path: {temp_events_path}")
    print(f"temp_claims_path: {temp_claims_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
