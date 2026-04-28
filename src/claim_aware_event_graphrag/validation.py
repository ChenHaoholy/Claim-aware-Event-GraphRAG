from __future__ import annotations

from .schemas import Chunk, Claim, Conflict, Event, TempClaim, TempEvent


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


def validate_temp_extraction(
    chunks: list[Chunk],
    temp_events: list[TempEvent],
    temp_claims: list[TempClaim],
) -> list[str]:
    errors: list[str] = []

    chunk_ids = {chunk.chunk_id for chunk in chunks}

    seen_temp_event_ids: set[str] = set()
    event_by_id: dict[str, TempEvent] = {}
    for event in temp_events:
        if event.temp_event_id in seen_temp_event_ids:
            errors.append(f"Duplicate temp_event_id: {event.temp_event_id}")
        seen_temp_event_ids.add(event.temp_event_id)
        event_by_id[event.temp_event_id] = event

        if event.chunk_id not in chunk_ids:
            errors.append(f"TempEvent {event.temp_event_id} references missing chunk_id {event.chunk_id}")
        if event.summary.strip() == "":
            errors.append(f"TempEvent {event.temp_event_id} has empty summary")

    seen_temp_claim_ids: set[str] = set()
    for claim in temp_claims:
        if claim.temp_claim_id in seen_temp_claim_ids:
            errors.append(f"Duplicate temp_claim_id: {claim.temp_claim_id}")
        seen_temp_claim_ids.add(claim.temp_claim_id)

        if claim.chunk_id not in chunk_ids:
            errors.append(f"TempClaim {claim.temp_claim_id} references missing chunk_id {claim.chunk_id}")
        if claim.source_chunk_id not in chunk_ids:
            errors.append(
                f"TempClaim {claim.temp_claim_id} references missing source_chunk_id {claim.source_chunk_id}"
            )
        if claim.chunk_id != claim.source_chunk_id:
            errors.append(
                f"TempClaim {claim.temp_claim_id} has mismatched chunk_id {claim.chunk_id} and source_chunk_id {claim.source_chunk_id}"
            )

        if claim.temp_event_id not in event_by_id:
            errors.append(
                f"TempClaim {claim.temp_claim_id} references missing temp_event_id {claim.temp_event_id}"
            )
        else:
            event = event_by_id[claim.temp_event_id]
            if claim.chunk_id != event.chunk_id:
                errors.append(
                    f"TempClaim {claim.temp_claim_id} chunk_id {claim.chunk_id} does not match TempEvent {event.temp_event_id} chunk_id {event.chunk_id}"
                )

        if claim.text.strip() == "":
            errors.append(f"TempClaim {claim.temp_claim_id} has empty text")
        if claim.claimant.strip() == "":
            errors.append(f"TempClaim {claim.temp_claim_id} has empty claimant")

    return errors



def validate_conflicts(
    events: list[Event],
    claims: list[Claim],
    conflicts: list[Conflict],
) -> list[str]:
    errors: list[str] = []

    event_ids = {event.event_id for event in events}
    claim_by_id = {claim.claim_id: claim for claim in claims}

    seen_conflict_ids: set[str] = set()
    for conflict in conflicts:
        if conflict.conflict_id in seen_conflict_ids:
            errors.append(f"Duplicate conflict_id: {conflict.conflict_id}")
        seen_conflict_ids.add(conflict.conflict_id)

        if conflict.event_id not in event_ids:
            errors.append(f"Conflict {conflict.conflict_id} references missing event_id {conflict.event_id}")

        linked_claims: list[Claim] = []
        for claim_id in conflict.claim_ids:
            claim = claim_by_id.get(claim_id)
            if claim is None:
                errors.append(f"Conflict {conflict.conflict_id} references missing claim_id {claim_id}")
            else:
                linked_claims.append(claim)

        if linked_claims:
            linked_event_ids = {claim.event_id for claim in linked_claims}
            if len(linked_event_ids) != 1:
                errors.append(
                    f"Conflict {conflict.conflict_id} has claim_ids that belong to multiple event_ids: {sorted(linked_event_ids)}"
                )
            elif conflict.event_id not in linked_event_ids:
                errors.append(
                    f"Conflict {conflict.conflict_id} event_id {conflict.event_id} does not match claim event_id {next(iter(linked_event_ids))}"
                )

            topic_counts: dict[str, int] = {}
            for claim in linked_claims:
                topic_counts[claim.topic] = topic_counts.get(claim.topic, 0) + 1
            majority_topic = max(topic_counts.items(), key=lambda x: x[1])[0]
            if conflict.topic != majority_topic:
                errors.append(
                    f"Conflict {conflict.conflict_id} topic {conflict.topic} does not match majority claim topic {majority_topic}"
                )

        if not conflict.is_conflict and conflict.severity != "none":
            errors.append(
                f"Conflict {conflict.conflict_id} has is_conflict=false but severity={conflict.severity}"
            )
        if conflict.is_conflict and conflict.severity == "none":
            errors.append(
                f"Conflict {conflict.conflict_id} has is_conflict=true but severity=none"
            )
        if conflict.explanation.strip() == "":
            errors.append(f"Conflict {conflict.conflict_id} has empty explanation")

    return errors
