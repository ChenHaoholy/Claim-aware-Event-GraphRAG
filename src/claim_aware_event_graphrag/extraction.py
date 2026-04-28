from __future__ import annotations

import json

from pydantic import ValidationError

from .llm import LLMClient
from .prompts import build_event_claim_extraction_prompt
from .schemas import Chunk, ExtractionResult, TempClaim, TempEvent


class ExtractionError(ValueError):
    """Raised when extraction output is invalid."""


def _prefix_local_id(chunk_id: str, local_id: str) -> str:
    return local_id if local_id.startswith(f"{chunk_id}_") else f"{chunk_id}_{local_id}"


def extract_from_chunk(chunk: Chunk, llm_client: LLMClient) -> ExtractionResult:
    prompt = build_event_claim_extraction_prompt(chunk)
    raw_output = llm_client.complete(prompt)

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ExtractionError(
            f"Chunk {chunk.chunk_id}: LLM output is not valid JSON (line {exc.lineno}, col {exc.colno})"
        ) from exc

    if not isinstance(payload, dict):
        raise ExtractionError(f"Chunk {chunk.chunk_id}: LLM output must be a JSON object")

    raw_events = payload.get("temp_events", [])
    raw_claims = payload.get("temp_claims", [])

    if not isinstance(raw_events, list) or not isinstance(raw_claims, list):
        raise ExtractionError(f"Chunk {chunk.chunk_id}: temp_events and temp_claims must be lists")

    local_to_prefixed_event_id: dict[str, str] = {}
    temp_events: list[TempEvent] = []

    for index, event in enumerate(raw_events, start=1):
        if not isinstance(event, dict):
            raise ExtractionError(f"Chunk {chunk.chunk_id}: temp_events[{index}] must be an object")

        local_event_id = event.get("temp_event_id")
        if not isinstance(local_event_id, str) or local_event_id.strip() == "":
            raise ExtractionError(f"Chunk {chunk.chunk_id}: temp_events[{index}].temp_event_id must be non-empty")

        prefixed_event_id = _prefix_local_id(chunk.chunk_id, local_event_id)
        local_to_prefixed_event_id[local_event_id] = prefixed_event_id
        local_to_prefixed_event_id[prefixed_event_id] = prefixed_event_id

        event_payload = {
            **event,
            "temp_event_id": prefixed_event_id,
            "chunk_id": chunk.chunk_id,
        }

        try:
            temp_events.append(TempEvent.model_validate(event_payload))
        except ValidationError as exc:
            raise ExtractionError(f"Chunk {chunk.chunk_id}: invalid temp event at index {index}: {exc}") from exc

    temp_claims: list[TempClaim] = []

    for index, claim in enumerate(raw_claims, start=1):
        if not isinstance(claim, dict):
            raise ExtractionError(f"Chunk {chunk.chunk_id}: temp_claims[{index}] must be an object")

        local_claim_id = claim.get("temp_claim_id")
        if not isinstance(local_claim_id, str) or local_claim_id.strip() == "":
            raise ExtractionError(f"Chunk {chunk.chunk_id}: temp_claims[{index}].temp_claim_id must be non-empty")

        local_event_id = claim.get("temp_event_id")
        if not isinstance(local_event_id, str) or local_event_id.strip() == "":
            raise ExtractionError(f"Chunk {chunk.chunk_id}: temp_claims[{index}].temp_event_id must be non-empty")

        prefixed_event_id = local_to_prefixed_event_id.get(local_event_id, _prefix_local_id(chunk.chunk_id, local_event_id))
        prefixed_claim_id = _prefix_local_id(chunk.chunk_id, local_claim_id)

        claim_payload = {
            **claim,
            "temp_claim_id": prefixed_claim_id,
            "temp_event_id": prefixed_event_id,
            "chunk_id": chunk.chunk_id,
            "source_chunk_id": chunk.chunk_id,
        }

        try:
            temp_claims.append(TempClaim.model_validate(claim_payload))
        except ValidationError as exc:
            raise ExtractionError(f"Chunk {chunk.chunk_id}: invalid temp claim at index {index}: {exc}") from exc

    try:
        return ExtractionResult.model_validate({"temp_events": temp_events, "temp_claims": temp_claims})
    except ValidationError as exc:
        raise ExtractionError(f"Chunk {chunk.chunk_id}: extraction result validation failed: {exc}") from exc


def extract_from_chunks(chunks: list[Chunk], llm_client: LLMClient) -> tuple[list[TempEvent], list[TempClaim]]:
    all_temp_events: list[TempEvent] = []
    all_temp_claims: list[TempClaim] = []

    for chunk in chunks:
        try:
            result = extract_from_chunk(chunk, llm_client)
        except Exception as exc:
            raise ExtractionError(f"Extraction failed for chunk {chunk.chunk_id}: {exc}") from exc

        all_temp_events.extend(result.temp_events)
        all_temp_claims.extend(result.temp_claims)

    return all_temp_events, all_temp_claims
