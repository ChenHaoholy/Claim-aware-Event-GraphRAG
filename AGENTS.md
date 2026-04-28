# AGENTS.md

## Project
- This repository is **Claim-aware Event GraphRAG**.
- Long-term goal: build an **Event → Claim → Evidence** graph-based QA system.

## Working principles for Codex
- Make changes in **small, testable steps**.
- Prefer explicit, readable, deterministic logic before adding complex components.
- Keep schemas simple and stable.
- Avoid over-engineering.

## Current focus
- Core objects at this stage:
  - `Chunk`
  - `Event`
  - `Claim`
  - `TempEvent`
  - `TempClaim`
  - `Conflict`
  - `GraphNode`
  - `GraphEdge`
- Keep graph construction file-based (JSONL), deterministic, and easy to inspect.

## Do NOT add unless explicitly requested
- Real LLM API integration
- Full GraphRAG orchestration
- Frontend/UI
- Database/storage layer

## Data/output conventions
- Use JSONL for intermediate artifacts whenever possible.
- Each pipeline step should provide:
  - runnable script(s)
  - test coverage
  - human-readable outputs / inspectable files

## Validation & testing
- Keep outputs traceable and verifiable.
- After changes, run `pytest` when environment allows.
- Do not silently swallow parsing or validation errors.

## Practical guardrails
- Keep modifications minimal and scoped to the requested step.
- Preserve backward compatibility unless explicitly asked to break it.
- Update docs when pipeline or schema assumptions change.
