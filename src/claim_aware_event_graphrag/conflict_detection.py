from __future__ import annotations

from collections import OrderedDict
import re
import string

from .schemas import Claim, Conflict, Event


class ConflictDetectionError(ValueError):
    """Raised when conflict detection cannot proceed."""


def group_claims_by_event_and_topic(
    claims: list[Claim],
) -> dict[tuple[str, str], list[Claim]]:
    grouped: "OrderedDict[tuple[str, str], list[Claim]]" = OrderedDict()

    for claim in claims:
        key = (claim.event_id, claim.topic)
        grouped.setdefault(key, []).append(claim)

    filtered = OrderedDict()
    for key, group in grouped.items():
        if len(group) >= 2:
            filtered[key] = group

    return dict(filtered)


def generate_conflict_candidates(
    claims: list[Claim],
) -> list[list[Claim]]:
    grouped = group_claims_by_event_and_topic(claims)
    candidates: list[list[Claim]] = []

    for (_, _), group_claims in grouped.items():
        dedup_by_claimant: "OrderedDict[str, Claim]" = OrderedDict()
        for claim in group_claims:
            claimant_key = claim.claimant.strip().lower()
            if claimant_key not in dedup_by_claimant:
                dedup_by_claimant[claimant_key] = claim

        if len(dedup_by_claimant) >= 2:
            candidates.append(list(dedup_by_claimant.values()))

    return candidates


def normalize_claim_text(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", lowered).strip()


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def detect_rule_based_conflict(
    event: Event,
    claims: list[Claim],
    conflict_index: int,
) -> Conflict:
    if len(claims) < 2:
        raise ConflictDetectionError("Conflict candidate must contain at least 2 claims")

    topic = claims[0].topic
    claim_ids = [claim.claim_id for claim in claims]
    normalized_texts = [normalize_claim_text(claim.text) for claim in claims]

    military_terms = ["military facility", "military target", "military site"]
    civilian_terms = ["civilian infrastructure", "civilian site", "civilian target"]

    no_casualty_terms = ["no casualties", "zero casualties"]
    casualty_terms = ["casualties", "killed", "dead"]

    low_damage_terms = ["no damage", "minor damage"]
    heavy_damage_terms = ["destroyed", "severe damage", "heavily damaged"]

    stable_terms = ["oil prices would not change", "no significant change", "remain stable"]
    rise_terms = ["oil prices could rise", "prices rose", "increase", "surge"]

    if topic == "target":
        has_military = any(_contains_any(text, military_terms) for text in normalized_texts)
        has_civilian = any(_contains_any(text, civilian_terms) for text in normalized_texts)
        if has_military and has_civilian:
            return Conflict(
                conflict_id=f"CF{conflict_index:03d}",
                event_id=event.event_id,
                claim_ids=claim_ids,
                topic=topic,
                is_conflict=True,
                severity="high",
                explanation="Target claims conflict: military target language and civilian target language both present.",
            )

    if topic == "casualty":
        has_no_casualty = any(_contains_any(text, no_casualty_terms) for text in normalized_texts)
        has_positive_casualty = any(
            _contains_any(text, casualty_terms) and (bool(re.search(r"\d", text)) or "killed" in text or "dead" in text)
            for text in normalized_texts
        )
        if has_no_casualty and has_positive_casualty:
            return Conflict(
                conflict_id=f"CF{conflict_index:03d}",
                event_id=event.event_id,
                claim_ids=claim_ids,
                topic=topic,
                is_conflict=True,
                severity="high",
                explanation="Casualty claims conflict: zero/no casualties vs reported casualties/killed/dead.",
            )

    if topic == "damage":
        has_low_damage = any(_contains_any(text, low_damage_terms) for text in normalized_texts)
        has_heavy_damage = any(_contains_any(text, heavy_damage_terms) for text in normalized_texts)
        if has_low_damage and has_heavy_damage:
            return Conflict(
                conflict_id=f"CF{conflict_index:03d}",
                event_id=event.event_id,
                claim_ids=claim_ids,
                topic=topic,
                is_conflict=True,
                severity="high",
                explanation="Damage claims conflict: low/no damage language and severe/destruction language both present.",
            )

    if topic == "economic_impact":
        has_stable = any(_contains_any(text, stable_terms) for text in normalized_texts)
        has_rise = any(_contains_any(text, rise_terms) for text in normalized_texts)
        if has_stable and has_rise:
            return Conflict(
                conflict_id=f"CF{conflict_index:03d}",
                event_id=event.event_id,
                claim_ids=claim_ids,
                topic=topic,
                is_conflict=True,
                severity="medium",
                explanation="Economic impact claims conflict: stability/no-change language conflicts with increase/surge language.",
            )

    if topic == "verification":
        if all("unverified" in text or "could not be independently verified" in text for text in normalized_texts):
            return Conflict(
                conflict_id=f"CF{conflict_index:03d}",
                event_id=event.event_id,
                claim_ids=claim_ids,
                topic=topic,
                is_conflict=False,
                severity="none",
                explanation="Verification claims indicate uncertainty rather than direct contradiction.",
            )

    stances = {claim.stance for claim in claims}
    if "deny" in stances and "assert" in stances:
        similarity_hits = 0
        for i in range(len(normalized_texts)):
            for j in range(i + 1, len(normalized_texts)):
                tokens_i = set(normalized_texts[i].split())
                tokens_j = set(normalized_texts[j].split())
                if tokens_i and tokens_j and len(tokens_i & tokens_j) >= 2:
                    similarity_hits += 1
        if similarity_hits > 0:
            return Conflict(
                conflict_id=f"CF{conflict_index:03d}",
                event_id=event.event_id,
                claim_ids=claim_ids,
                topic=topic,
                is_conflict=True,
                severity="medium",
                explanation="Stance-based contradiction detected: assert and deny claims with overlapping subject wording.",
            )

    return Conflict(
        conflict_id=f"CF{conflict_index:03d}",
        event_id=event.event_id,
        claim_ids=claim_ids,
        topic=topic,
        is_conflict=False,
        severity="none",
        explanation="No direct contradiction detected by rule-based checks.",
    )


def detect_conflicts(
    events: list[Event],
    claims: list[Claim],
) -> list[Conflict]:
    candidates = generate_conflict_candidates(claims)
    event_by_id = {event.event_id: event for event in events}

    conflicts: list[Conflict] = []
    for index, candidate_claims in enumerate(candidates, start=1):
        event_id = candidate_claims[0].event_id
        event = event_by_id.get(event_id)
        if event is None:
            raise ConflictDetectionError(
                f"Conflict candidate references missing event_id {event_id}"
            )
        conflicts.append(detect_rule_based_conflict(event, candidate_claims, index))

    return conflicts
