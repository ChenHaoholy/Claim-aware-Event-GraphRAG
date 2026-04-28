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

Current repository work is centered on Steps 1–7 deterministic foundations.

---

## 3) Current Schemas

### Chunk
Fields:
- `chunk_id: str`
- `doc_id: str`
- `source: str | None`
- `date: str | None`
- `text: str`

### Event
Fields:
- `event_id: str`
- `time: str | None`
- `type: Literal[military, diplomatic, economic, maritime, nuclear, humanitarian, political, other]`
- `summary: str`
- `actors: list[str]`
- `location: str | None`

### Claim
Fields:
- `claim_id: str`
- `event_id: str`
- `claimant: str`
- `text: str`
- `topic: Literal[responsibility, target, casualty, damage, economic_impact, policy, verification, cause, response, other]`
- `stance: Literal[assert, deny, uncertain, report]`
- `source_chunk_id: str`

### TempEvent
Fields:
- `temp_event_id: str`
- `chunk_id: str`
- `time: str | None`
- `type: Event.type literal`
- `summary: str`
- `actors: list[str]`
- `location: str | None`

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

### ExtractionResult
Fields:
- `temp_events: list[TempEvent]`
- `temp_claims: list[TempClaim]`

### Conflict
Fields:
- `conflict_id: str`
- `event_id: str`
- `claim_ids: list[str]`
- `topic: Claim.topic literal`
- `is_conflict: bool`
- `severity: Literal[low, medium, high, none]`
- `explanation: str`

### GraphNode
Fields:
- `node_id: str`
- `node_type: Literal[event, claim, chunk, actor, location, conflict]`
- `label: str`
- `properties: dict[str, Any]`

### GraphEdge
Fields:
- `edge_id: str`
- `source_id: str`
- `target_id: str`
- `edge_type: Literal[ABOUT, SUPPORTED_BY, MADE_BY, INVOLVES_ACTOR, OCCURRED_AT, HAS_CONFLICT, CONFLICTS_WITH]`
- `properties: dict[str, Any]`

### RetrievalResult
Fields:
- `question: str`
- `relevant_event_ids: list[str]`
- `relevant_claim_ids: list[str]`
- `relevant_chunk_ids: list[str]`
- `relevant_conflict_ids: list[str]`
- `debug_info: dict[str, Any]`

### AnswerResult
Fields:
- `question: str`
- `conclusion: str`
- `key_events: list[dict]`
- `claims_by_actor: dict[str, list[dict]]`
- `conflicts_and_uncertainty: list[dict]`
- `evidence: list[dict]`
- `limitations: list[str]`

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
- `data/processed/conflicts.jsonl`

### Graph data
- `data/graph/nodes.jsonl`
- `data/graph/edges.jsonl`

---

## 5) Graph Construction Rules (Step 5)
Node creation:
- Event -> event node
- Claim -> claim node
- Chunk -> chunk node
- actor strings -> actor node (normalized)
- non-empty location -> location node (normalized)
- Conflict -> conflict node

Edge creation:
- Claim `ABOUT` Event
- Claim `SUPPORTED_BY` Chunk
- Claim `MADE_BY` Actor
- Event `INVOLVES_ACTOR` Actor
- Event `OCCURRED_AT` Location
- Event `HAS_CONFLICT` Conflict
- Conflict `CONFLICTS_WITH` Claim

---

## 6) Retrieval Rules (Step 6)
Inputs:
- `question` text
- chunks/events/claims/conflicts datasets
- graph nodes/edges files as upstream context artifacts

Outputs:
- `RetrievalResult` (IDs only + debug_info)

Rule-based scoring:
- event score from summary/actors/location/type token overlap
- claim score from text/claimant/topic/stance overlap
- chunk score from text overlap
- conflict score from topic/explanation/related claims + conflict-oriented query hints

Expansion rules:
- selected event -> add its claims
- selected claim -> add its event and source chunk
- selected conflict -> add related claims, event, and source chunks

Current limitations:
- keyword overlap scoring only
- no embeddings
- no graph traversal engine
- no hybrid retrieval yet

---

## 7) Answer Generation Rules (Step 7)
Inputs:
- retrieval context expanded from `RetrievalResult`

Outputs:
- `AnswerResult`
- markdown answer text with sections:
  - Conclusion
  - Key Events
  - Claims by Actor
  - Conflicts and Uncertainty
  - Evidence
  - Limitations

Rules:
- deterministic template-based synthesis
- use only retrieved context
- do not fabricate missing facts
- no real LLM usage in current step

Current limitations:
- no semantic rewriting beyond template formatting
- quality depends on retrieval quality

---

## 8) Validation Principles
- IDs should be unique in their scope.
- References must resolve (no dangling event/chunk/graph references).
- Claims must be traceable to both event and chunk.
- Each step output should be human-inspectable (JSONL artifacts + scripts/tests).

---

## 9) Out of Scope for Now
- Real LLM API integration
- Frontend
- Database
- Neo4j / vector database runtime
- Full GraphRAG orchestration
