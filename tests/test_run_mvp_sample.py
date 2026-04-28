from pathlib import Path
import shutil

import pytest

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


def test_run_mvp_sample_pipeline_default_mock_end_to_end() -> None:
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
    assert len(answers) == 3
    assert all(isinstance(item, str) and item.strip() != "" for item in answers)

    assert any("What happened near Meridian Port?" in answer for answer in answers)
    assert any("Oil prices rose after the incident." in answer for answer in answers)

    major_events = [event for event in events if event.type == "military"]
    assert any(event.time is not None for event in major_events)
    assert any(event.location == "Meridian Port" for event in major_events)


def test_skip_extraction_does_not_call_extraction(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(__file__).resolve().parents[1]

    # ensure temp files exist first
    run_mvp_sample_pipeline(root=root, llm_provider="mock", skip_extraction=False)

    def _boom(*args, **kwargs):
        raise AssertionError("extract_from_chunks should not be called when --skip-extraction is used")

    monkeypatch.setattr("claim_aware_event_graphrag.extraction.extract_from_chunks", _boom)

    result = run_mvp_sample_pipeline(root=root, skip_extraction=True)
    assert len(result["temp_events"]) > 0


def test_skip_extraction_missing_temp_files_raises() -> None:
    root = Path(__file__).resolve().parents[1]
    processed_dir = root / "data" / "processed"
    temp_events_path = processed_dir / "temp_events.jsonl"
    temp_claims_path = processed_dir / "temp_claims.jsonl"

    backup_events = processed_dir / "temp_events.jsonl.bak_test"
    backup_claims = processed_dir / "temp_claims.jsonl.bak_test"

    processed_dir.mkdir(parents=True, exist_ok=True)

    if temp_events_path.exists():
        shutil.move(str(temp_events_path), str(backup_events))
    if temp_claims_path.exists():
        shutil.move(str(temp_claims_path), str(backup_claims))

    try:
        with pytest.raises(RuntimeError, match="skip-extraction"):
            run_mvp_sample_pipeline(root=root, skip_extraction=True)
    finally:
        if backup_events.exists():
            shutil.move(str(backup_events), str(temp_events_path))
        if backup_claims.exists():
            shutil.move(str(backup_claims), str(temp_claims_path))
