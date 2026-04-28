from claim_aware_event_graphrag.graph_builder import build_graph
from claim_aware_event_graphrag.schemas import Chunk, Claim, Conflict, Event


def _chunk(chunk_id: str) -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id=f"doc_{chunk_id}", source=None, date=None, text="evidence")


def _event(event_id: str = "E001") -> Event:
    return Event(
        event_id=event_id,
        time="2026-03-04",
        type="military",
        summary="Strike at Meridian Port",
        actors=["U.S.", "State B"],
        location="Meridian Port",
    )


def _claim(claim_id: str, event_id: str = "E001", chunk_id: str = "chunk_001") -> Claim:
    return Claim(
        claim_id=claim_id,
        event_id=event_id,
        claimant="United States",
        text="The strike targeted a military facility.",
        topic="target",
        stance="assert",
        source_chunk_id=chunk_id,
    )


def _conflict() -> Conflict:
    return Conflict(
        conflict_id="CF001",
        event_id="E001",
        claim_ids=["C001", "C002"],
        topic="target",
        is_conflict=True,
        severity="high",
        explanation="Conflicting target claims.",
    )


def test_build_graph_generates_nodes_and_edges() -> None:
    chunks = [_chunk("chunk_001")]
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict()]

    nodes, edges = build_graph(chunks, events, claims, conflicts)

    assert len(nodes) > 0
    assert len(edges) > 0


def test_all_core_node_types_are_generated() -> None:
    chunks = [_chunk("chunk_001")]
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict()]

    nodes, _ = build_graph(chunks, events, claims, conflicts)

    node_types = {node.node_type for node in nodes}
    assert {"event", "claim", "chunk", "actor", "location", "conflict"}.issubset(node_types)


def test_expected_edge_types_exist() -> None:
    chunks = [_chunk("chunk_001")]
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict()]

    _, edges = build_graph(chunks, events, claims, conflicts)

    edge_keys = {(edge.source_id, edge.target_id, edge.edge_type) for edge in edges}

    assert ("claim:C001", "event:E001", "ABOUT") in edge_keys
    assert ("claim:C001", "chunk:chunk_001", "SUPPORTED_BY") in edge_keys
    assert any(edge_type == "MADE_BY" for _, _, edge_type in edge_keys)
    assert any(edge_type == "INVOLVES_ACTOR" for _, _, edge_type in edge_keys)
    assert ("event:E001", "location:meridian port", "OCCURRED_AT") in edge_keys
    assert ("conflict:CF001", "claim:C001", "CONFLICTS_WITH") in edge_keys


def test_no_duplicate_nodes_or_edges() -> None:
    chunks = [_chunk("chunk_001")]
    events = [_event()]
    claims = [_claim("C001"), _claim("C002")]
    conflicts = [_conflict()]

    nodes, edges = build_graph(chunks, events, claims, conflicts)

    node_ids = [node.node_id for node in nodes]
    edge_keys = [(edge.source_id, edge.target_id, edge.edge_type) for edge in edges]

    assert len(node_ids) == len(set(node_ids))
    assert len(edge_keys) == len(set(edge_keys))
