from __future__ import annotations

from .schemas import Chunk


def build_event_claim_extraction_prompt(chunk: Chunk) -> str:
    return f"""你是一个用于 Claim-aware Event GraphRAG 系统的事件与声明抽取助手。

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
{{
  "temp_events": [
    {{
      "temp_event_id": "e1",
      "time": "YYYY-MM-DD or null",
      "type": "military | diplomatic | economic | maritime | nuclear | humanitarian | political | other",
      "summary": "short event summary",
      "actors": ["actor1", "actor2"],
      "location": "location or null"
    }}
  ],
  "temp_claims": [
    {{
      "temp_claim_id": "c1",
      "temp_event_id": "e1",
      "claimant": "actor making the claim",
      "text": "concise claim text",
      "topic": "responsibility | target | casualty | damage | economic_impact | policy | verification | cause | response | other",
      "stance": "assert | deny | uncertain | report"
    }}
  ]
}}

Chunk metadata:
chunk_id: {chunk.chunk_id}
date: {chunk.date}
source: {chunk.source}

Chunk text:
{chunk.text}

注意：
- LLM 输出中不需要 chunk_id 和 source_chunk_id，程序后处理时自动补充。
- temp_event_id 和 temp_claim_id 后处理时要加 chunk_id 前缀，避免跨 chunk 冲突。"""
