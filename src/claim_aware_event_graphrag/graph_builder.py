from __future__ import annotations

from .event_merge import normalize_actor, normalize_text
from .schemas import (
    Chunk,
    Claim,
    Conflict,
    Event,
    GraphEdge,
    GraphNode,
)


def _normalize_location(value: str) -> str:
    return normalize_text(value)


def build_graph(
    chunks: list[Chunk],
    events: list[Event],
    claims: list[Claim],
    conflicts: list[Conflict],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    node_map: dict[str, GraphNode] = {}

    def add_node(node: GraphNode) -> None:
        if node.node_id not in node_map:
            node_map[node.node_id] = node

    # Core nodes
    for chunk in chunks:
        add_node(
            GraphNode(
                node_id=f"chunk:{chunk.chunk_id}",
                node_type="chunk",
                label=chunk.chunk_id,
                properties={
                    "doc_id": chunk.doc_id,
                    "source": chunk.source,
                    "date": chunk.date,
                    "text": chunk.text,
                },
            )
        )

    for event in events:
        add_node(
            GraphNode(
                node_id=f"event:{event.event_id}",
                node_type="event",
                label=event.summary,
                properties={
                    "event_id": event.event_id,
                    "time": event.time,
                    "type": event.type,
                    "location": event.location,
                },
            )
        )

        for actor in event.actors:
            normalized_actor = normalize_actor(actor)
            if normalized_actor == "":
                continue
            add_node(
                GraphNode(
                    node_id=f"actor:{normalized_actor}",
                    node_type="actor",
                    label=actor,
                    properties={"normalized": normalized_actor},
                )
            )

        if event.location is not None and normalize_text(event.location) != "":
            norm_loc = _normalize_location(event.location)
            add_node(
                GraphNode(
                    node_id=f"location:{norm_loc}",
                    node_type="location",
                    label=event.location,
                    properties={"normalized": norm_loc},
                )
            )

    for claim in claims:
        add_node(
            GraphNode(
                node_id=f"claim:{claim.claim_id}",
                node_type="claim",
                label=claim.text,
                properties={
                    "claim_id": claim.claim_id,
                    "event_id": claim.event_id,
                    "claimant": claim.claimant,
                    "topic": claim.topic,
                    "stance": claim.stance,
                    "source_chunk_id": claim.source_chunk_id,
                },
            )
        )

        normalized_claimant = normalize_actor(claim.claimant)
        if normalized_claimant != "":
            add_node(
                GraphNode(
                    node_id=f"actor:{normalized_claimant}",
                    node_type="actor",
                    label=claim.claimant,
                    properties={"normalized": normalized_claimant},
                )
            )

    for conflict in conflicts:
        add_node(
            GraphNode(
                node_id=f"conflict:{conflict.conflict_id}",
                node_type="conflict",
                label=conflict.explanation,
                properties={
                    "conflict_id": conflict.conflict_id,
                    "event_id": conflict.event_id,
                    "topic": conflict.topic,
                    "is_conflict": conflict.is_conflict,
                    "severity": conflict.severity,
                },
            )
        )

    edge_tuples: list[tuple[str, str, str, dict[str, object]]] = []

    # Claim edges
    for claim in claims:
        claim_node = f"claim:{claim.claim_id}"
        event_node = f"event:{claim.event_id}"
        chunk_node = f"chunk:{claim.source_chunk_id}"
        actor_node = f"actor:{normalize_actor(claim.claimant)}"

        edge_tuples.append((claim_node, event_node, "ABOUT", {}))
        edge_tuples.append((claim_node, chunk_node, "SUPPORTED_BY", {}))
        if normalize_actor(claim.claimant) != "":
            edge_tuples.append((claim_node, actor_node, "MADE_BY", {}))

    # Event edges
    for event in events:
        event_node = f"event:{event.event_id}"
        for actor in event.actors:
            normalized_actor = normalize_actor(actor)
            if normalized_actor == "":
                continue
            actor_node = f"actor:{normalized_actor}"
            edge_tuples.append((event_node, actor_node, "INVOLVES_ACTOR", {}))

        if event.location is not None and normalize_text(event.location) != "":
            loc_node = f"location:{_normalize_location(event.location)}"
            edge_tuples.append((event_node, loc_node, "OCCURRED_AT", {}))

    # Conflict edges
    for conflict in conflicts:
        conflict_node = f"conflict:{conflict.conflict_id}"
        event_node = f"event:{conflict.event_id}"
        edge_tuples.append((event_node, conflict_node, "HAS_CONFLICT", {}))
        for claim_id in conflict.claim_ids:
            claim_node = f"claim:{claim_id}"
            edge_tuples.append((conflict_node, claim_node, "CONFLICTS_WITH", {}))

    # Deduplicate edges while preserving order
    seen_edges: set[tuple[str, str, str]] = set()
    deduped_edges: list[tuple[str, str, str, dict[str, object]]] = []
    for source_id, target_id, edge_type, properties in edge_tuples:
        key = (source_id, target_id, edge_type)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        deduped_edges.append((source_id, target_id, edge_type, properties))

    edges: list[GraphEdge] = []
    for idx, (source_id, target_id, edge_type, properties) in enumerate(deduped_edges, start=1):
        edges.append(
            GraphEdge(
                edge_id=f"edge_{idx:06d}",
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                properties=properties,
            )
        )

    nodes = list(node_map.values())
    nodes.sort(key=lambda n: n.node_id)
    return nodes, edges
