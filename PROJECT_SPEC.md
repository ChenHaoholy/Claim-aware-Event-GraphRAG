# PROJECT_SPEC.md

## 1) Project Goal
Claim-aware Event GraphRAG aims to build an event-centered QA system where:
- **Event** captures what happened,
- **Claim** captures who said what,
- **Chunk** captures evidence source text.

The design emphasizes stable intermediate outputs and verification at every step.

---

## 2) Pipeline Roadmap
- **Step 1**: schema + sample data + validation
- **Step 2**: chunk-level Event + Claim extraction
- **Step 3**: temp event merge + claim canonicalization
- **Step 4**: claim conflict detection
- **Step 5**: graph construction
- **Step 6**: retrieval
- **Step 7**: answer generation

Current repository work is centered on Steps 1–3 foundations.

---

## 3) Current Schemas

### Chunk
Fields:
- `chunk_id: str`
- `doc_id: str`
- `source: str | None`
- `date: str | None`
- `text: str`

Purpose:
- Atomic evidence unit from source text.

### Event
Fields:
- `event_id: str`
- `time: str | None`
- `type: Literal[military, diplomatic, economic, maritime, nuclear, humanitarian, political, other]`
- `summary: str`
- `actors: list[str]`
- `location: str | None`

Purpose:
- Canonical event representation after merge.

### Claim
Fields:
- `claim_id: str`
- `event_id: str`
- `claimant: str`
- `text: str`
- `topic: Literal[responsibility, target, casualty, damage, economic_impact, policy, verification, cause, response, other]`
- `stance: Literal[assert, deny, uncertain, report]`
- `source_chunk_id: str`

Purpose:
- Canonical statement linked to an Event and evidence chunk.

### TempEvent
Fields:
- `temp_event_id: str`
- `chunk_id: str`
- `time: str | None`
- `type: Event.type literal`
- `summary: str`
- `actors: list[str]`
- `location: str | None`

Purpose:
- Per-chunk extracted event candidate before merge.

### TempClaim
Fields:
- `temp_claim_id: str`
- `temp_event_id: str`
- `chunk_id: str`
- `claimant: str`
- `text: str`
- `topic: Claim.topic literal`
- `stance: Claim.stance literal`
- `source_chunk_id: str`

Purpose:
- Per-chunk extracted claim candidate before canonicalization.

### ExtractionResult
Fields:
- `temp_events: list[TempEvent]`
- `temp_claims: list[TempClaim]`

Purpose:
- Container for one chunk extraction output.

---

## 4) JSONL Files

### Sample data
- `data/sample/chunks.jsonl`
- `data/sample/events.jsonl`
- `data/sample/claims.jsonl`

### Processed data
- `data/processed/temp_events.jsonl`
- `data/processed/temp_claims.jsonl`
- `data/processed/events.jsonl`
- `data/processed/claims.jsonl`
- `data/processed/temp_event_mapping.jsonl`

---

## 5) Validation Principles
- IDs should be unique in their scope.
- References must resolve (no dangling event/chunk references).
- Claims must be traceable to both event and chunk.
- Each step output should be human-inspectable (JSONL artifacts + scripts/tests).

---

## 6) Out of Scope for Now
- Real LLM API integration
- Frontend
- Database
- Full GraphRAG runtime
