from claim_aware_event_graphrag.schemas import GraphEdge, GraphNode
from claim_aware_event_graphrag.validation import validate_graph


def _valid_nodes() -> list[GraphNode]:
    return [
        GraphNode(node_id="event:E001", node_type="event", label="Event 1", properties={}),
        GraphNode(node_id="claim:C001", node_type="claim", label="Claim 1", properties={}),
    ]


def _valid_edges() -> list[GraphEdge]:
    return [
        GraphEdge(
            edge_id="edge_000001",
            source_id="claim:C001",
            target_id="event:E001",
            edge_type="ABOUT",
            properties={},
        )
    ]


def test_valid_graph_passes_validation() -> None:
    errors = validate_graph(_valid_nodes(), _valid_edges())
    assert errors == []


def test_duplicate_node_id_detected() -> None:
    nodes = _valid_nodes() + [
        GraphNode(node_id="event:E001", node_type="event", label="Dup", properties={})
    ]
    errors = validate_graph(nodes, _valid_edges())
    assert "Duplicate node_id: event:E001" in errors


def test_duplicate_edge_id_detected() -> None:
    edges = _valid_edges() + [
        GraphEdge(
            edge_id="edge_000001",
            source_id="claim:C001",
            target_id="event:E001",
            edge_type="ABOUT",
            properties={},
        )
    ]
    errors = validate_graph(_valid_nodes(), edges)
    assert "Duplicate edge_id: edge_000001" in errors


def test_missing_source_id_detected() -> None:
    edges = [
        GraphEdge(
            edge_id="edge_000010",
            source_id="claim:C999",
            target_id="event:E001",
            edge_type="ABOUT",
            properties={},
        )
    ]
    errors = validate_graph(_valid_nodes(), edges)
    assert "Edge edge_000010 references missing source_id claim:C999" in errors


def test_missing_target_id_detected() -> None:
    edges = [
        GraphEdge(
            edge_id="edge_000011",
            source_id="claim:C001",
            target_id="event:E999",
            edge_type="ABOUT",
            properties={},
        )
    ]
    errors = validate_graph(_valid_nodes(), edges)
    assert "Edge edge_000011 references missing target_id event:E999" in errors


def test_empty_label_detected() -> None:
    nodes = [
        GraphNode(node_id="event:E001", node_type="event", label="Event", properties={}),
        GraphNode.model_construct(node_id="claim:C001", node_type="claim", label="", properties={}),
    ]
    errors = validate_graph(nodes, _valid_edges())
    assert any("empty label" in err for err in errors)
