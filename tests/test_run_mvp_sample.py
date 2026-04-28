from pathlib import Path

from claim_aware_event_graphrag.jsonl import (
    load_claims,
    load_conflicts,
    load_events,
    load_graph_edges,
    load_graph_nodes,
    load_temp_claims,
    load_temp_events,
)
from scripts.run_mvp_sample import run_mvp_sample_pipeline


def test_run_mvp_sample_pipeline_end_to_end() -> None:
    root = Path(__file__).resolve().parents[1]

    result = run_mvp_sample_pipeline(root=root)

    processed_dir = root / "data" / "processed"
    graph_dir = root / "data" / "graph"

    temp_events = load_temp_events(processed_dir / "temp_events.jsonl")
    temp_claims = load_temp_claims(processed_dir / "temp_claims.jsonl")
    events = load_events(processed_dir / "events.jsonl")
    claims = load_claims(processed_dir / "claims.jsonl")
    conflicts = load_conflicts(processed_dir / "conflicts.jsonl")
    nodes = load_graph_nodes(graph_dir / "nodes.jsonl")
    edges = load_graph_edges(graph_dir / "edges.jsonl")

    assert len(temp_events) > 0
    assert len(temp_claims) > 0
    assert len(events) > 0
    assert len(claims) > 0
    assert len(conflicts) > 0
    assert len(nodes) > 0
    assert len(edges) > 0

    answers = result["answers_markdown"]
    assert isinstance(answers, list)
    assert len(answers) >= 1
    assert all(isinstance(item, str) and item.strip() != "" for item in answers)
