from __future__ import annotations

import re
import string

from .schemas import Chunk, Claim, Conflict, Event, RetrievalResult

STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "to",
    "and",
    "or",
    "is",
    "are",
    "was",
    "were",
}

CONFLICT_HINTS = {
    "conflict",
    "dispute",
    "contradiction",
    "争议",
    "冲突",
    "矛盾",
    "unverified",
    "verify",
}


def normalize_query(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", lowered).strip()


def tokenize_query(text: str) -> set[str]:
    normalized = normalize_query(text)
    tokens = set(normalized.split()) if normalized else set()
    return {token for token in tokens if token not in STOPWORDS}


def _token_overlap_score(query_tokens: set[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    text_tokens = tokenize_query(text)
    if not text_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)


def score_event(question: str, event: Event) -> float:
    query_tokens = tokenize_query(question)
    score = 0.0

    score += 1.0 * _token_overlap_score(query_tokens, event.summary)
    score += 1.5 * _token_overlap_score(query_tokens, " ".join(event.actors))
    score += 1.5 * _token_overlap_score(query_tokens, event.location or "")
    score += 1.2 * _token_overlap_score(query_tokens, event.type)

    return score


def score_claim(question: str, claim: Claim) -> float:
    query_tokens = tokenize_query(question)
    score = 0.0

    score += 1.0 * _token_overlap_score(query_tokens, claim.text)
    score += 1.2 * _token_overlap_score(query_tokens, claim.claimant)
    score += 1.4 * _token_overlap_score(query_tokens, claim.topic)
    score += 0.5 * _token_overlap_score(query_tokens, claim.stance)

    if query_tokens & CONFLICT_HINTS:
        score += 0.3

    return score


def score_chunk(question: str, chunk: Chunk) -> float:
    query_tokens = tokenize_query(question)
    return _token_overlap_score(query_tokens, chunk.text)


def score_conflict(question: str, conflict: Conflict, claims_by_id: dict[str, Claim]) -> float:
    query_tokens = tokenize_query(question)
    score = 0.0

    if query_tokens & CONFLICT_HINTS:
        score += 0.8

    score += 1.2 * _token_overlap_score(query_tokens, conflict.topic)
    score += 1.0 * _token_overlap_score(query_tokens, conflict.explanation)

    related_text = " ".join(
        claims_by_id[claim_id].text for claim_id in conflict.claim_ids if claim_id in claims_by_id
    )
    score += 1.0 * _token_overlap_score(query_tokens, related_text)

    return score


def _top_scored_ids(
    scored_items: list[tuple[str, float]],
    top_k: int,
) -> tuple[list[str], list[dict[str, object]]]:
    scored_items.sort(key=lambda x: (-x[1], x[0]))
    picked = [item_id for item_id, score in scored_items[:top_k] if score > 0]
    debug = [{"id": item_id, "score": round(score, 4)} for item_id, score in scored_items]
    return picked, debug


def retrieve_context(
    question: str,
    chunks: list[Chunk],
    events: list[Event],
    claims: list[Claim],
    conflicts: list[Conflict],
    top_k_events: int = 5,
    top_k_claims: int = 8,
    top_k_chunks: int = 8,
    top_k_conflicts: int = 5,
) -> RetrievalResult:
    query_tokens = sorted(tokenize_query(question))

    claims_by_id = {claim.claim_id: claim for claim in claims}
    events_by_id = {event.event_id: event for event in events}
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}

    scored_events = [(event.event_id, score_event(question, event)) for event in events]
    scored_claims = [(claim.claim_id, score_claim(question, claim)) for claim in claims]
    scored_chunks = [(chunk.chunk_id, score_chunk(question, chunk)) for chunk in chunks]
    scored_conflicts = [
        (conflict.conflict_id, score_conflict(question, conflict, claims_by_id)) for conflict in conflicts
    ]

    selected_event_ids, debug_events = _top_scored_ids(scored_events, top_k_events)
    selected_claim_ids, debug_claims = _top_scored_ids(scored_claims, top_k_claims)
    selected_chunk_ids, debug_chunks = _top_scored_ids(scored_chunks, top_k_chunks)
    selected_conflict_ids, debug_conflicts = _top_scored_ids(scored_conflicts, top_k_conflicts)

    expansion_notes: list[str] = []

    # Expansion: event -> claims
    for event_id in list(selected_event_ids):
        for claim in claims:
            if claim.event_id == event_id and claim.claim_id not in selected_claim_ids:
                selected_claim_ids.append(claim.claim_id)
                expansion_notes.append(f"Added claim {claim.claim_id} from selected event {event_id}")

    # Expansion: claim -> event/chunk
    for claim_id in list(selected_claim_ids):
        claim = claims_by_id.get(claim_id)
        if claim is None:
            continue

        if claim.event_id not in selected_event_ids and claim.event_id in events_by_id:
            selected_event_ids.append(claim.event_id)
            expansion_notes.append(f"Added event {claim.event_id} from selected claim {claim_id}")

        if claim.source_chunk_id not in selected_chunk_ids and claim.source_chunk_id in chunks_by_id:
            selected_chunk_ids.append(claim.source_chunk_id)
            expansion_notes.append(
                f"Added chunk {claim.source_chunk_id} from selected claim {claim_id}"
            )

    # Expansion: conflict -> claims/event/chunks
    conflicts_by_id = {conflict.conflict_id: conflict for conflict in conflicts}
    for conflict_id in list(selected_conflict_ids):
        conflict = conflicts_by_id.get(conflict_id)
        if conflict is None:
            continue

        if conflict.event_id not in selected_event_ids and conflict.event_id in events_by_id:
            selected_event_ids.append(conflict.event_id)
            expansion_notes.append(
                f"Added event {conflict.event_id} from selected conflict {conflict_id}"
            )

        for claim_id in conflict.claim_ids:
            if claim_id in claims_by_id and claim_id not in selected_claim_ids:
                selected_claim_ids.append(claim_id)
                expansion_notes.append(
                    f"Added claim {claim_id} from selected conflict {conflict_id}"
                )

            claim = claims_by_id.get(claim_id)
            if claim and claim.source_chunk_id in chunks_by_id and claim.source_chunk_id not in selected_chunk_ids:
                selected_chunk_ids.append(claim.source_chunk_id)
                expansion_notes.append(
                    f"Added chunk {claim.source_chunk_id} from conflict-linked claim {claim_id}"
                )

    def _dedup_preserve_order(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    result = RetrievalResult(
        question=question,
        relevant_event_ids=_dedup_preserve_order(selected_event_ids),
        relevant_claim_ids=_dedup_preserve_order(selected_claim_ids),
        relevant_chunk_ids=_dedup_preserve_order(selected_chunk_ids),
        relevant_conflict_ids=_dedup_preserve_order(selected_conflict_ids),
        debug_info={
            "query_tokens": query_tokens,
            "scored_events": debug_events,
            "scored_claims": debug_claims,
            "scored_chunks": debug_chunks,
            "scored_conflicts": debug_conflicts,
            "expansion_notes": expansion_notes,
        },
    )

    return result


def format_retrieval_result(
    result: RetrievalResult,
    chunks: list[Chunk],
    events: list[Event],
    claims: list[Claim],
    conflicts: list[Conflict],
) -> dict:
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    events_by_id = {event.event_id: event for event in events}
    claims_by_id = {claim.claim_id: claim for claim in claims}
    conflicts_by_id = {conflict.conflict_id: conflict for conflict in conflicts}

    return {
        "question": result.question,
        "events": [
            events_by_id[event_id].model_dump(mode="json")
            for event_id in result.relevant_event_ids
            if event_id in events_by_id
        ],
        "claims": [
            claims_by_id[claim_id].model_dump(mode="json")
            for claim_id in result.relevant_claim_ids
            if claim_id in claims_by_id
        ],
        "chunks": [
            chunks_by_id[chunk_id].model_dump(mode="json")
            for chunk_id in result.relevant_chunk_ids
            if chunk_id in chunks_by_id
        ],
        "conflicts": [
            conflicts_by_id[conflict_id].model_dump(mode="json")
            for conflict_id in result.relevant_conflict_ids
            if conflict_id in conflicts_by_id
        ],
        "debug_info": result.debug_info,
    }
