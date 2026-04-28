# PROMPTS.md

This file stores reusable prompt templates for future LLM-based stages.
Current codebase uses mock/rule-based implementations by default.

---

## 1) Event + Claim Extraction Prompt (Step 2)

### Purpose
Given one `Chunk`, extract `temp_events` and `temp_claims` in strict JSON.

### Template

你是一个用于 Claim-aware Event GraphRAG 系统的事件与声明抽取助手。

请从文本 chunk 中抽取 temp_events 和 temp_claims。

Event 是发生了、被报道发生了、或被实质讨论的一件事。
Claim 是某个主体对某个事件提出的声明、否认、预测、评估或不确定性表达。

允许的 event type：
military, diplomatic, economic, maritime, nuclear, humanitarian, political, other

允许的 claim topic：
responsibility, target, casualty, damage, economic_impact, policy, verification, cause, response, other

允许的 claim stance：
assert, deny, uncertain, report

规则：
1. 不要把 claim 当作事实。
2. 每个 claim 必须绑定一个 temp_event_id。
3. 如果文本讨论油价、航运、制裁、市场反应等影响，也可以抽成 economic 或 maritime event。
4. 缺失信息用 null。
5. 只输出 JSON，不要解释。
6. claim_id 和 event_id 不需要全局唯一，只需要在当前 chunk 内唯一。
7. 输出字段必须严格符合 schema。
8. 不要编造文本中没有的信息。

输出格式：
{
  "temp_events": [
    {
      "temp_event_id": "e1",
      "time": "YYYY-MM-DD or null",
      "type": "military | diplomatic | economic | maritime | nuclear | humanitarian | political | other",
      "summary": "short event summary",
      "actors": ["actor1", "actor2"],
      "location": "location or null"
    }
  ],
  "temp_claims": [
    {
      "temp_claim_id": "c1",
      "temp_event_id": "e1",
      "claimant": "actor making the claim",
      "text": "concise claim text",
      "topic": "responsibility | target | casualty | damage | economic_impact | policy | verification | cause | response | other",
      "stance": "assert | deny | uncertain | report"
    }
  ]
}

Chunk metadata:
chunk_id: {chunk.chunk_id}
date: {chunk.date}
source: {chunk.source}

Chunk text:
{chunk.text}

注意：
- 输出中不需要 `chunk_id` 和 `source_chunk_id`（由后处理补充）。
- `temp_event_id` 和 `temp_claim_id` 会由后处理加上 chunk_id 前缀。

---

## 2) Event Coreference / Merge Judge Prompt (Future)

### Purpose
Future replacement for rule-based `events_maybe_same`.
Judge if two `TempEvent` objects refer to the same underlying event.

### Template

You are an event coreference judge for a Claim-aware Event GraphRAG pipeline.
Decide whether Event A and Event B refer to the same real-world event.

Output JSON only:
{
  "same_event": true/false,
  "confidence": 0.0-1.0,
  "reason": "short explanation"
}

Guidelines:
- Compare event type, time, location, actors, and summary semantics.
- Do not merge merely related but distinct events (e.g., military strike vs economic reaction).
- Be conservative: if uncertain, return false with lower confidence.

Event A:
{event_a_json}

Event B:
{event_b_json}

---

## 3) Conflict Judge Prompt (Future)

### Purpose
Future replacement/augmentation for rule-based conflict detector.
Judge whether claims in one `(event_id, topic)` group are contradictory.

### Template

You are a contradiction judge for claims about the same event and topic.
Given multiple claims, decide if they contain direct contradiction.

Output JSON only:
{
  "is_conflict": true/false,
  "severity": "low|medium|high|none",
  "explanation": "short rationale"
}

Rules:
- Distinguish uncertainty from contradiction.
- "report" vs "assert" is not automatically contradiction.
- Contradictions should reference same semantic object when possible.
- If no direct contradiction, return severity "none".

Event:
{event_json}

Claims:
{claims_json}

---

## 4) Final Answer Prompt (Future QA stage)

### Purpose
Future answer synthesis prompt over canonical events/claims/conflicts/evidence.
Not active in current repository stage.

### Template

You are an analyst assistant.
Answer the user's question using only provided structured evidence.

Requirements:
- Separate facts, claims, and uncertainty.
- Cite which event(s), claim(s), and evidence chunk(s) support each statement.
- If conflicting claims exist, present both and explain conflict status.
- Do not fabricate missing facts.
- If evidence is insufficient, say so clearly.

Output format:
1) Direct answer (concise)
2) Evidence summary (bullets)
3) Conflicts/uncertainty (bullets)
4) Structured references: event_ids, claim_ids, chunk_ids
