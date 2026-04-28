"""Claim-aware Event GraphRAG package."""

from .event_merge import (
    canonicalize_claims,
    cluster_temp_events,
    events_maybe_same,
    make_canonical_event,
    merge_temp_extraction,
)
from .extraction import extract_from_chunk, extract_from_chunks
from .schemas import (
    Chunk,
    Claim,
    Event,
    ExtractionResult,
    TempClaim,
    TempEvent,
)
from .validation import validate_dataset, validate_temp_extraction

__all__ = [
    "Chunk",
    "Event",
    "Claim",
    "TempEvent",
    "TempClaim",
    "ExtractionResult",
    "validate_dataset",
    "validate_temp_extraction",
    "extract_from_chunk",
    "extract_from_chunks",
    "events_maybe_same",
    "cluster_temp_events",
    "make_canonical_event",
    "canonicalize_claims",
    "merge_temp_extraction",
]
