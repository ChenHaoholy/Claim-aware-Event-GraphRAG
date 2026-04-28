from __future__ import annotations

from collections import Counter
import re
import string

from .schemas import Claim, Event, TempClaim, TempEvent


class EventMergeError(ValueError):
    """Raised when merge or canonicalization cannot proceed."""


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_actor(actor: str) -> str:
    normalized = normalize_text(actor)
    aliases = {
        "u.s.": "united states",
        "us": "united states",
        "usa": "united states",
        "america": "united states",
        "israeli government": "israel",
        "iranian government": "iran",
    }
    return aliases.get(normalized, normalized)


def actor_overlap(a: list[str], b: list[str]) -> float:
    set_a = {normalize_actor(actor) for actor in a if normalize_actor(actor) != ""}
    set_b = {normalize_actor(actor) for actor in b if normalize_actor(actor) != ""}

    if not set_a and not set_b:
        return 0.0

    union = set_a | set_b
    if not union:
        return 0.0

    return len(set_a & set_b) / len(union)


def _tokenize(value: str) -> set[str]:
    normalized = normalize_text(value)
    tokens: list[str] = []
    for token in normalized.split():
        cleaned = token.strip(string.punctuation)
        if cleaned:
            tokens.append(cleaned)
    return set(tokens)


def simple_token_similarity(a: str, b: str) -> float:
    set_a = _tokenize(a)
    set_b = _tokenize(b)

    if not set_a and not set_b:
        return 0.0

    union = set_a | set_b
    if not union:
        return 0.0

    return len(set_a & set_b) / len(union)


def events_maybe_same(a: TempEvent, b: TempEvent) -> tuple[bool, float, str]:
    summary_similarity = simple_token_similarity(a.summary, b.summary)
    same_type = a.type == b.type
    same_time = a.time is not None and b.time is not None and normalize_text(a.time) == normalize_text(b.time)
    both_time_present_and_different = (
        a.time is not None and b.time is not None and normalize_text(a.time) != normalize_text(b.time)
    )
    same_location = (
        a.location is not None
        and b.location is not None
        and normalize_text(a.location) == normalize_text(b.location)
    )
    both_location_present_and_different = (
        a.location is not None
        and b.location is not None
        and normalize_text(a.location) != normalize_text(b.location)
    )
    overlap = actor_overlap(a.actors, b.actors)

    score = 0.0
    reasons: list[str] = []

    if same_type:
        score += 0.25
        reasons.append("same_type")

    if same_time:
        score += 0.20
        reasons.append("same_time")

    if same_location:
        score += 0.20
        reasons.append("same_location")

    if overlap >= 0.5:
        score += 0.15
        reasons.append(f"actor_overlap={overlap:.2f}")

    if summary_similarity >= 0.3:
        score += 0.20
        reasons.append(f"summary_similarity={summary_similarity:.2f}")

    # Hard guards
    if {a.type, b.type} == {"economic", "military"}:
        return False, score, "guard: do_not_merge_economic_and_military"

    if {a.type, b.type} == {"diplomatic", "military"}:
        return False, score, "guard: do_not_merge_diplomatic_and_military"

    if not same_type and summary_similarity < 0.6:
        return False, score, "guard: different_type_low_summary_similarity"

    if both_time_present_and_different and both_location_present_and_different:
        return False, score, "guard: different_time_and_location"

    same_event = score >= 0.60
    reason = ",".join(reasons) if reasons else "insufficient_score"
    return same_event, score, reason


def cluster_temp_events(temp_events: list[TempEvent]) -> list[list[TempEvent]]:
    if not temp_events:
        return []

    parent = list(range(len(temp_events)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        root_x = find(x)
        root_y = find(y)
        if root_x == root_y:
            return
        if root_x < root_y:
            parent[root_y] = root_x
        else:
            parent[root_x] = root_y

    for i in range(len(temp_events)):
        for j in range(i + 1, len(temp_events)):
            same_event, _, _ = events_maybe_same(temp_events[i], temp_events[j])
            if same_event:
                union(i, j)

    grouped: dict[int, list[tuple[int, TempEvent]]] = {}
    for idx, event in enumerate(temp_events):
        root = find(idx)
        grouped.setdefault(root, []).append((idx, event))

    clusters = []
    for root in sorted(grouped.keys()):
        cluster_items = sorted(grouped[root], key=lambda x: x[0])
        clusters.append([item[1] for item in cluster_items])

    return clusters


def _most_common_non_empty(values: list[str | None]) -> str | None:
    filtered = [value for value in values if value is not None and normalize_text(value) != ""]
    if not filtered:
        return None
    counts = Counter(filtered)
    return counts.most_common(1)[0][0]


def make_canonical_event(cluster: list[TempEvent], event_index: int) -> Event:
    if not cluster:
        raise EventMergeError("Cannot canonicalize empty event cluster")

    event_id = f"E{event_index:03d}"
    time = _most_common_non_empty([event.time for event in cluster])

    type_counts = Counter(event.type for event in cluster)
    event_type = type_counts.most_common(1)[0][0]

    location = _most_common_non_empty([event.location for event in cluster])

    actor_map: dict[str, str] = {}
    for event in cluster:
        for actor in event.actors:
            if normalize_text(actor) == "":
                continue
            key = normalize_actor(actor)
            if key and key not in actor_map:
                actor_map[key] = actor.strip()
    actors = list(actor_map.values())

    summary = max(cluster, key=lambda e: len(normalize_text(e.summary))).summary

    return Event(
        event_id=event_id,
        time=time,
        type=event_type,
        summary=summary,
        actors=actors,
        location=location,
    )


def canonicalize_claims(
    temp_claims: list[TempClaim],
    temp_event_to_event_id: dict[str, str],
) -> list[Claim]:
    claims: list[Claim] = []

    for index, temp_claim in enumerate(temp_claims, start=1):
        event_id = temp_event_to_event_id.get(temp_claim.temp_event_id)
        if event_id is None:
            raise EventMergeError(
                f"TempClaim {temp_claim.temp_claim_id} references missing temp_event_id mapping: {temp_claim.temp_event_id}"
            )

        claims.append(
            Claim(
                claim_id=f"C{index:03d}",
                event_id=event_id,
                claimant=temp_claim.claimant,
                text=temp_claim.text,
                topic=temp_claim.topic,
                stance=temp_claim.stance,
                source_chunk_id=temp_claim.source_chunk_id,
            )
        )

    return claims


def merge_temp_extraction(
    temp_events: list[TempEvent],
    temp_claims: list[TempClaim],
) -> tuple[list[Event], list[Claim], dict[str, str]]:
    clusters = cluster_temp_events(temp_events)

    events: list[Event] = []
    temp_event_to_event_id: dict[str, str] = {}

    for idx, cluster in enumerate(clusters, start=1):
        canonical_event = make_canonical_event(cluster, event_index=idx)
        events.append(canonical_event)
        for temp_event in cluster:
            temp_event_to_event_id[temp_event.temp_event_id] = canonical_event.event_id

    claims = canonicalize_claims(temp_claims, temp_event_to_event_id)

    return events, claims, temp_event_to_event_id
