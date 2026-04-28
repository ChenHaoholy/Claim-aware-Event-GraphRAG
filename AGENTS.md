# AGENTS.md

This file defines repository-level instructions for coding agents (Codex, etc.).

## Scope
- Applies to the entire repository.

## Project intent
This repository is a staged, verifiable buildout of a **Claim-aware Event GraphRAG** pipeline.
Current implemented focus is deterministic data processing with stable intermediate artifacts.

## Hard constraints
- Keep architecture simple and inspectable.
- Preserve JSONL-based intermediate outputs for each step.
- Prefer deterministic/rule-based logic in early stages.
- Keep components replaceable (especially LLM client interfaces).

## Must NOT do (unless explicitly requested)
- Do **not** implement full GraphRAG orchestration.
- Do **not** add retrieval/vector DB.
- Do **not** add frontend/UI.
- Do **not** connect real LLM APIs by default.
- Do **not** add conflict-resolution intelligence beyond requested MVP rules.
- Do **not** introduce a database layer.
- Do **not** silently swallow parsing/validation errors.

## Code and design rules
- Python 3.10+ compatible.
- Pydantic-based schemas are the source of truth for data contracts.
- Keep modules focused:
  - `schemas.py`: data contracts only
  - `jsonl.py`: JSONL I/O + typed loaders
  - `validation.py`: cross-record integrity checks
  - `extraction.py`/`event_merge.py`/`conflict_detection.py`: stage logic
- Prefer explicit, readable errors with context (path, line number, IDs).
- Keep function behavior stable and testable.
- Avoid over-engineering and unnecessary abstractions.

## Testing expectations
When changing code/docs, run the relevant checks if environment allows:
1. `python scripts/validate_sample.py`
2. `python scripts/extract_sample.py`
3. `python scripts/merge_sample.py`
4. `python scripts/validate_processed.py`
5. `python scripts/detect_conflicts_sample.py`
6. `pytest`

If environment limitations block execution (e.g., missing dependencies/network), report clearly.

## Output artifacts to preserve
- `data/sample/*.jsonl`
- `data/processed/temp_events.jsonl`
- `data/processed/temp_claims.jsonl`
- `data/processed/temp_event_mapping.jsonl`
- `data/processed/events.jsonl`
- `data/processed/claims.jsonl`
- `data/processed/conflicts.jsonl`

## Documentation discipline
- Keep `PROJECT_SPEC.md` updated when schema/pipeline changes.
- Keep `PROMPTS.md` updated when prompt contracts or output JSON formats change.
- Keep README command sequence aligned with scripts.
