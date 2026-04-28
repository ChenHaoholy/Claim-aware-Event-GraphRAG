from __future__ import annotations

from collections import defaultdict

from .schemas import AnswerResult


def _safe_list(value: object) -> list[dict]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def generate_answer_from_context(retrieval_context: dict) -> AnswerResult:
    question = str(retrieval_context.get("question", "")).strip()
    events = _safe_list(retrieval_context.get("events"))
    claims = _safe_list(retrieval_context.get("claims"))
    chunks = _safe_list(retrieval_context.get("chunks"))
    conflicts = _safe_list(retrieval_context.get("conflicts"))

    if events:
        conclusion = f"Retrieved {len(events)} event(s), {len(claims)} claim(s), and {len(conflicts)} conflict record(s) relevant to the question."
    else:
        conclusion = "No strongly relevant structured context was retrieved for this question."

    key_events: list[dict[str, object]] = []
    for event in events:
        key_events.append(
            {
                "event_id": event.get("event_id"),
                "type": event.get("type"),
                "time": event.get("time"),
                "location": event.get("location"),
                "summary": event.get("summary"),
                "actors": event.get("actors", []),
            }
        )

    claims_by_actor_map: dict[str, list[dict[str, object]]] = defaultdict(list)
    for claim in claims:
        actor = str(claim.get("claimant", "Unknown")).strip() or "Unknown"
        claims_by_actor_map[actor].append(
            {
                "claim_id": claim.get("claim_id"),
                "event_id": claim.get("event_id"),
                "topic": claim.get("topic"),
                "stance": claim.get("stance"),
                "text": claim.get("text"),
            }
        )

    conflicts_and_uncertainty: list[dict[str, object]] = []
    for conflict in conflicts:
        conflicts_and_uncertainty.append(
            {
                "conflict_id": conflict.get("conflict_id"),
                "event_id": conflict.get("event_id"),
                "topic": conflict.get("topic"),
                "is_conflict": conflict.get("is_conflict"),
                "severity": conflict.get("severity"),
                "explanation": conflict.get("explanation"),
                "claim_ids": conflict.get("claim_ids", []),
            }
        )

    evidence: list[dict[str, object]] = []
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        evidence.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "doc_id": chunk.get("doc_id"),
                "source": chunk.get("source"),
                "date": chunk.get("date"),
                "text_snippet": text[:220],
            }
        )

    limitations = [
        "Rule-based retrieval and synthesis may miss semantically relevant evidence.",
        "No real LLM reasoning is applied in this stage.",
        "Answer uses only retrieved context; if retrieval misses facts, answer will be incomplete.",
    ]

    return AnswerResult(
        question=question,
        conclusion=conclusion,
        key_events=key_events,
        claims_by_actor=dict(claims_by_actor_map),
        conflicts_and_uncertainty=conflicts_and_uncertainty,
        evidence=evidence,
        limitations=limitations,
    )


def format_answer_markdown(answer: AnswerResult) -> str:
    lines: list[str] = []
    lines.append(f"# Answer: {answer.question}")
    lines.append("")
    lines.append("## Conclusion")
    lines.append(answer.conclusion)
    lines.append("")

    lines.append("## Key Events")
    if answer.key_events:
        for event in answer.key_events:
            lines.append(
                f"- **{event.get('event_id')}** ({event.get('type')}) @ {event.get('location')} [{event.get('time')}]: {event.get('summary')}"
            )
    else:
        lines.append("- No events retrieved.")
    lines.append("")

    lines.append("## Claims by Actor")
    if answer.claims_by_actor:
        for actor, actor_claims in answer.claims_by_actor.items():
            lines.append(f"- **{actor}**")
            for claim in actor_claims:
                lines.append(
                    f"  - ({claim.get('claim_id')}) [{claim.get('topic')}/{claim.get('stance')}] {claim.get('text')}"
                )
    else:
        lines.append("- No claims retrieved.")
    lines.append("")

    lines.append("## Conflicts and Uncertainty")
    if answer.conflicts_and_uncertainty:
        for conflict in answer.conflicts_and_uncertainty:
            lines.append(
                f"- **{conflict.get('conflict_id')}** event={conflict.get('event_id')} topic={conflict.get('topic')} conflict={conflict.get('is_conflict')} severity={conflict.get('severity')}: {conflict.get('explanation')}"
            )
    else:
        lines.append("- No conflict records retrieved.")
    lines.append("")

    lines.append("## Evidence")
    if answer.evidence:
        for ev in answer.evidence:
            lines.append(
                f"- **{ev.get('chunk_id')}** ({ev.get('source')}, {ev.get('date')}): {ev.get('text_snippet')}"
            )
    else:
        lines.append("- No evidence chunks retrieved.")
    lines.append("")

    lines.append("## Limitations")
    for limitation in answer.limitations:
        lines.append(f"- {limitation}")

    return "\n".join(lines)
