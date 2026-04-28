"""Claim-aware Event GraphRAG package."""

from .answer_generation import format_answer_markdown, generate_answer_from_context
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
from .retrieval import (
    format_retrieval_result,
    normalize_query,
    retrieve_context,
    score_chunk,
    score_claim,
    score_conflict,
    score_event,
    tokenize_query,
)
from .schemas import (
    AnswerResult,
    Chunk,
    Claim,
    Conflict,
    Event,
    ExtractionResult,
    GraphEdge,
    GraphNode,
    RetrievalResult,
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
    "RetrievalResult",
    "AnswerResult",
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
    "normalize_query",
    "tokenize_query",
    "score_event",
    "score_claim",
    "score_chunk",
    "score_conflict",
    "retrieve_context",
    "format_retrieval_result",
    "generate_answer_from_context",
    "format_answer_markdown",
]
