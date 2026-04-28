from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.graph_builder import build_graph
    from claim_aware_event_graphrag.jsonl import (
        load_chunks,
        load_claims,
        load_conflicts,
        load_events,
        write_jsonl,
    )
    from claim_aware_event_graphrag.validation import validate_graph

    chunks_path = root / "data" / "sample" / "chunks.jsonl"
    events_path = root / "data" / "processed" / "events.jsonl"
    claims_path = root / "data" / "processed" / "claims.jsonl"
    conflicts_path = root / "data" / "processed" / "conflicts.jsonl"

    if not (events_path.exists() and claims_path.exists() and conflicts_path.exists()):
        print(
            "Missing processed files. Please run: python scripts/extract_sample.py, python scripts/merge_sample.py, and python scripts/detect_conflicts_sample.py"
        )
        return 1

    chunks = load_chunks(chunks_path)
    events = load_events(events_path)
    claims = load_claims(claims_path)
    conflicts = load_conflicts(conflicts_path)

    nodes, edges = build_graph(chunks, events, claims, conflicts)

    out_dir = root / "data" / "graph"
    nodes_path = out_dir / "nodes.jsonl"
    edges_path = out_dir / "edges.jsonl"

    write_jsonl(nodes_path, [node.model_dump(mode="json") for node in nodes])
    write_jsonl(edges_path, [edge.model_dump(mode="json") for edge in edges])

    errors = validate_graph(nodes, edges)

    print(f"chunks: {len(chunks)}")
    print(f"events: {len(events)}")
    print(f"claims: {len(claims)}")
    print(f"conflicts: {len(conflicts)}")
    print(f"nodes: {len(nodes)}")
    print(f"edges: {len(edges)}")

    if errors:
        print("validation: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("validation: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
