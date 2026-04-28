from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python scripts/retrieve_sample.py "<question>"')
        return 1

    question = " ".join(sys.argv[1:]).strip()
    if question == "":
        print("Question must not be empty")
        return 1

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.jsonl import (
        load_chunks,
        load_claims,
        load_conflicts,
        load_events,
        load_graph_edges,
        load_graph_nodes,
    )
    from claim_aware_event_graphrag.retrieval import format_retrieval_result, retrieve_context

    chunks_path = root / "data" / "sample" / "chunks.jsonl"
    events_path = root / "data" / "processed" / "events.jsonl"
    claims_path = root / "data" / "processed" / "claims.jsonl"
    conflicts_path = root / "data" / "processed" / "conflicts.jsonl"
    graph_nodes_path = root / "data" / "graph" / "nodes.jsonl"
    graph_edges_path = root / "data" / "graph" / "edges.jsonl"

    if not (events_path.exists() and claims_path.exists() and conflicts_path.exists() and graph_nodes_path.exists() and graph_edges_path.exists()):
        print(
            "Missing processed/graph files. Please run: python scripts/extract_sample.py, python scripts/merge_sample.py, python scripts/detect_conflicts_sample.py, python scripts/build_graph_sample.py"
        )
        return 1

    chunks = load_chunks(chunks_path)
    events = load_events(events_path)
    claims = load_claims(claims_path)
    conflicts = load_conflicts(conflicts_path)
    # Graph files are loaded to ensure upstream graph artifacts exist and are parseable.
    _ = load_graph_nodes(graph_nodes_path)
    _ = load_graph_edges(graph_edges_path)

    result = retrieve_context(question, chunks, events, claims, conflicts)
    formatted = format_retrieval_result(result, chunks, events, claims, conflicts)

    print(json.dumps(formatted, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
