from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract temp events/claims from any chunk JSONL file")
    parser.add_argument("--chunks", required=True, help="Input chunks.jsonl path")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--llm", default="mock", choices=["mock", "deepseek"], help="LLM provider")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.extraction import extract_from_chunks
    from claim_aware_event_graphrag.jsonl import load_chunks, write_jsonl
    from claim_aware_event_graphrag.llm import get_llm_client

    chunks_path = Path(args.chunks)
    output_dir = Path(args.output_dir)
    temp_events_path = output_dir / "temp_events.jsonl"
    temp_claims_path = output_dir / "temp_claims.jsonl"

    chunks = load_chunks(chunks_path)
    llm_client = get_llm_client(args.llm)

    temp_events, temp_claims = extract_from_chunks(chunks, llm_client)

    write_jsonl(temp_events_path, [event.model_dump(mode="json") for event in temp_events])
    write_jsonl(temp_claims_path, [claim.model_dump(mode="json") for claim in temp_claims])

    print(f"llm_provider: {args.llm}")
    print(f"chunks_path: {chunks_path}")
    print(f"output_dir: {output_dir}")
    print(f"chunks: {len(chunks)}")
    print(f"temp_events: {len(temp_events)}")
    print(f"temp_claims: {len(temp_claims)}")
    print(f"temp_events_path: {temp_events_path}")
    print(f"temp_claims_path: {temp_claims_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
