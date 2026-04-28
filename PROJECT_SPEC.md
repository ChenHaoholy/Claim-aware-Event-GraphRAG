# PROJECT_SPEC.md

## 1) Project overview
Claim-aware Event GraphRAG is being built in incremental, verifiable steps.
Current repository scope covers deterministic data modeling and processing from evidence chunks to:
- extracted temporary events/claims,
- canonical merged events/claims,
- rule-based conflict detection results.

The system intentionally emphasizes inspectable intermediate JSONL artifacts.

---

## 2) Core schemas

### Chunk
Represents an evidence text segment.

Fields:
- `chunk_id: str`
- `doc_id: str`
- `source: str | None`
- `date: str | None`
- `text: str`

Key constraints:
- `chunk_id`, `doc_id`, `text` non-empty.

### Event (canonical)
Represents a normalized event after merge.

Fields:
- `event_id: str`
- `time: str | None`
- `type: Literal[military, diplomatic, economic, maritime, nuclear, humanitarian, political, other]`
- `summary: str`
- `actors: list[str]`
- `location: str | None`

Key constraints:
- `event_id`, `summary` non-empty.
- `actors` can be empty list, but cannot contain empty strings.

### Claim (canonical)
Represents a statement about a canonical event.

Fields:
- `claim_id: str`
- `event_id: str`
- `claimant: str`
- `text: str`
- `topic: Literal[responsibility, target, casualty, damage, economic_impact, policy, verification, cause, response, other]`
- `stance: Literal[assert, deny, uncertain, report]`
- `source_chunk_id: str`

Key constraints:
- key string fields non-empty.

### TempEvent
Per-chunk temporary event extraction output.

Fields:
- `temp_event_id: str`
- `chunk_id: str`
- `time: str | None`
- `type: Event.type literal`
- `summary: str`
- `actors: list[str]`
- `location: str | None`

Key constraints:
- `temp_event_id`, `chunk_id`, `summary` non-empty.
- `actors` cannot contain empty strings.

### TempClaim
Per-chunk temporary claim extraction output.

Fields:
- `temp_claim_id: str`
- `temp_event_id: str`
- `chunk_id: str`
- `claimant: str`
- `text: str`
- `topic: Claim.topic literal`
- `stance: Claim.stance literal`
- `source_chunk_id: str`

Key constraints:
- key string fields non-empty.
- `source_chunk_id == chunk_id`.

### ExtractionResult
Container for one chunk extraction call.

Fields:
- `temp_events: list[TempEvent]`
- `temp_claims: list[TempClaim]`

Key constraints:
- every `TempClaim.temp_event_id` must exist in `temp_events`.
- empty lists are valid.

### Conflict
Conflict analysis result for one candidate claim group.

Fields:
- `conflict_id: str` (e.g., `CF001`)
- `event_id: str`
- `claim_ids: list[str]` (>=2)
- `topic: Claim.topic literal`
- `is_conflict: bool`
- `severity: Literal[low, medium, high, none]`
- `explanation: str`

Key constraints:
- `conflict_id`, `event_id`, `explanation` non-empty.
- `claim_ids` must contain at least 2 IDs.
- if `is_conflict == false` then `severity == "none"`.
- if `is_conflict == true` then `severity != "none"`.

---

## 3) Pipeline steps

### Step 1 — Schema + sample + validation
Inputs:
- `data/sample/chunks.jsonl`
- `data/sample/events.jsonl`
- `data/sample/claims.jsonl`

Outputs/checks:
- schema validation and dataset integrity checks (`validate_dataset`).

### Step 2 — Chunk-level extraction
Input:
- sample chunks JSONL.

Processing:
- prompt build (`prompts.py`)
- `LLMClient` call (default `MockLLMClient`)
- normalize IDs and auto-fill chunk/source references

Outputs:
- `data/processed/temp_events.jsonl`
- `data/processed/temp_claims.jsonl`

### Step 3 — Event merge + claim canonicalization
Inputs:
- temp events/claims.

Processing:
- rule-based event similarity + clustering
- canonical event creation (`E001...`)
- temp claim mapping to canonical claim (`C001...`)

Outputs:
- `data/processed/events.jsonl`
- `data/processed/claims.jsonl`
- `data/processed/temp_event_mapping.jsonl`

### Step 4 — Claim conflict detection
Inputs:
- canonical events/claims.

Processing:
- group claims by `(event_id, topic)`
- keep groups with >=2 claims and >=2 distinct claimants
- rule-based contradiction checks per topic

Outputs:
- `data/processed/conflicts.jsonl` (includes both true/false conflict decisions for debugging)

---

## 4) Validation layers
- JSONL parse validation (file path + line number errors).
- Schema-level validation (Pydantic models).
- Cross-record validation:
  - `validate_dataset`
  - `validate_temp_extraction`
  - `validate_conflicts`

---

## 5) Non-goals (current stage)
- No GraphRAG runtime orchestration.
- No retrieval system / vector index.
- No final QA answer generation pipeline.
- No frontend.
- No real LLM API usage by default.
- No DB persistence layer.

---

## 6) Main commands
```bash
python scripts/validate_sample.py
python scripts/extract_sample.py
python scripts/merge_sample.py
python scripts/validate_processed.py
python scripts/detect_conflicts_sample.py
pytest
```
