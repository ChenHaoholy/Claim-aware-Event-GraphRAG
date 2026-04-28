from __future__ import annotations

from .schemas import Chunk


def build_event_claim_extraction_prompt(chunk: Chunk) -> str:
    return f"""你是一个用于 Claim-aware Event GraphRAG 系统的事件与声明抽取助手。

任务：从当前 chunk 中抽取 temp_events 和 temp_claims。

定义：
- Event：发生了、被报道发生了、或被实质讨论的一件事。
- Claim：某个主体对事件提出的声明、否认、预测、评估或不确定性表达。

允许的 event type：
military, diplomatic, economic, maritime, nuclear, humanitarian, political, other

允许的 claim topic：
responsibility, target, casualty, damage, economic_impact, policy, verification, cause, response, other

允许的 claim stance：
assert, deny, uncertain, report

硬性规则（必须遵守）：
1. 必须尽量抽取文本中的所有 claims，不要只抽最显眼的一条。
2. 如果一句话包含多个 claim，必须拆开为多条 claim。
   例如："targeted a military warehouse, not civilian facilities"
   至少应拆为：
   - military warehouse was targeted（topic=target, stance=assert）
   - civilian facilities were not targeted（topic=target 或 damage, stance=deny）
3. economic impact 相关说法统一归入 topic=economic_impact，包括但不限于：
   - oil prices rose
   - insurance premiums increased
   - port operations slowed
   - shipping costs increased
4. verification / cannot verify / not independently confirmed / unverified
   应使用：topic=verification, stance=uncertain。
5. diplomatic calls / calls for restraint / emergency dialogue
   应抽成 diplomatic event，并抽取 response 或 policy claim。
6. claimant 尽量使用具体主体，不要泛化。优先保留文本里的主体名称，
   如：Defense spokesperson, Local authority, Energy analysts, Monitoring group, Neighboring states。
   只有文本本身没有更具体主体时，才可使用 officials 等泛化主体。
7. 如果 chunk 中同时包含 event 和 claim，claim 必须绑定到该 chunk 的 temp_event_id。
8. 不要把 claim 当作事实，不要编造文本中没有的信息。
9. 缺失信息用 null。
10. 只输出 JSON，不要解释。
11. claim_id 和 event_id 只需在当前 chunk 内唯一。
12. 输出字段必须严格符合 schema。

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
