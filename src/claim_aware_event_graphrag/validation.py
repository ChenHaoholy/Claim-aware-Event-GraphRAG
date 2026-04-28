from __future__ import annotations

from .schemas import Chunk, Claim, Event


def validate_dataset(
    chunks: list[Chunk],
    events: list[Event],
    claims: list[Claim],
) -> list[str]:
    errors: list[str] = []

    seen_chunk_ids: set[str] = set()
    for chunk in chunks:
        if chunk.chunk_id in seen_chunk_ids:
            errors.append(f"Duplicate chunk_id: {chunk.chunk_id}")
        seen_chunk_ids.add(chunk.chunk_id)
        if chunk.text.strip() == "":
            errors.append(f"Chunk {chunk.chunk_id} has empty text")

    seen_event_ids: set[str] = set()
    for event in events:
        if event.event_id in seen_event_ids:
            errors.append(f"Duplicate event_id: {event.event_id}")
        seen_event_ids.add(event.event_id)
        if event.summary.strip() == "":
            errors.append(f"Event {event.event_id} has empty summary")
        for actor in event.actors:
            if actor.strip() == "":
                errors.append(f"Event {event.event_id} has empty actor")

    seen_claim_ids: set[str] = set()
    for claim in claims:
        if claim.claim_id in seen_claim_ids:
            errors.append(f"Duplicate claim_id: {claim.claim_id}")
        seen_claim_ids.add(claim.claim_id)

        if claim.text.strip() == "":
            errors.append(f"Claim {claim.claim_id} has empty text")
        if claim.claimant.strip() == "":
            errors.append(f"Claim {claim.claim_id} has empty claimant")

        if claim.event_id not in seen_event_ids:
            errors.append(f"Claim {claim.claim_id} references missing event_id {claim.event_id}")
        if claim.source_chunk_id not in seen_chunk_ids:
            errors.append(
                f"Claim {claim.claim_id} references missing source_chunk_id {claim.source_chunk_id}"
            )

    return errors
