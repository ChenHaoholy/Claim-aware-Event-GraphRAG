"""Claim-aware Event GraphRAG package."""

from .conflict_detection import (
    detect_conflicts,
    detect_rule_based_conflict,
    generate_conflict_candidates,
    group_claims_by_event_and_topic,
)
from .event_merge import (
    canonicalize_claims,
    cluster_temp_events,
    events_maybe_same,
    make_canonical_event,
    merge_temp_extraction,
)
from .extraction import extract_from_chunk, extract_from_chunks
from .graph_builder import build_graph
from .schemas import (
    Chunk,
    Claim,
    Conflict,
    Event,
    ExtractionResult,
    GraphEdge,
    GraphNode,
    TempClaim,
    TempEvent,
)
from .validation import (
    validate_conflicts,
    validate_dataset,
    validate_graph,
    validate_temp_extraction,
)

__all__ = [
    "Chunk",
    "Event",
    "Claim",
    "Conflict",
    "GraphNode",
    "GraphEdge",
    "TempEvent",
    "TempClaim",
    "ExtractionResult",
    "validate_dataset",
    "validate_temp_extraction",
    "validate_conflicts",
    "validate_graph",
    "extract_from_chunk",
    "extract_from_chunks",
    "events_maybe_same",
    "cluster_temp_events",
    "make_canonical_event",
    "canonicalize_claims",
    "merge_temp_extraction",
    "group_claims_by_event_and_topic",
    "generate_conflict_candidates",
    "detect_rule_based_conflict",
    "detect_conflicts",
    "build_graph",
]
