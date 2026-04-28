# PROMPTS.md

This file stores reusable LLM prompt templates.
Current implementation can stay mock/rule-based; templates here are for future integration.

---

## 1) Event + Claim Extraction Prompt

**Goal**: From one chunk, extract `temp_events` and `temp_claims` in strict JSON.

Template (simplified):
- Input: chunk metadata + chunk text.
- Output JSON fields:
  - `temp_events[]`: `temp_event_id`, `time`, `type`, `summary`, `actors`, `location`
  - `temp_claims[]`: `temp_claim_id`, `temp_event_id`, `claimant`, `text`, `topic`, `stance`
- Rules:
  - Do not treat claims as facts.
  - Every claim must link to one `temp_event_id`.
  - Use `null` for missing info.
  - Output JSON only.

---

## 2) Event Coreference Prompt

**Goal**: Judge whether two temp events refer to the same underlying event.

Suggested output JSON:
```json
{
  "same_event": true,
  "confidence": 0.0,
  "reason": "..."
}
```

---

## 3) Canonical Event Generation Prompt

**Goal**: Given a cluster of temp events, produce one canonical Event draft.

Suggested output JSON:
```json
{
  "time": null,
  "type": "military",
  "summary": "...",
  "actors": ["..."],
  "location": null
}
```

Note: in deterministic mode this can remain rule-based; prompt kept for future replacement.

---

## 4) Claim Conflict Judge Prompt

**Goal**: Given one event and multiple claims in same topic, judge contradiction.

Suggested output JSON:
```json
{
  "is_conflict": false,
  "severity": "none",
  "explanation": "..."
}
```

---

## 5) Final Answer Generation Prompt

**Goal**: Synthesize a user-facing answer from structured evidence.

Requirements:
- separate facts vs claims vs uncertainty,
- cite event/claim/chunk references,
- show conflicting claims when present,
- avoid fabrication.

Suggested structure:
1. Direct answer
2. Evidence summary
3. Uncertainty/conflicts
4. Structured references
