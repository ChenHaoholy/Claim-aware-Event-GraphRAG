# Claim-aware Event GraphRAG

## 项目目标
本项目用于构建一个“事件（Event）—声明（Claim）—证据片段（Chunk）”图谱问答系统。

## 当前阶段
- **Step 1**：schema + sample data + validation
- **Step 2**：Chunk 级 Event + Claim 抽取（temp_events / temp_claims）
- **Step 3**：Event Merge and Claim Canonicalization
- **Step 4**：Claim Conflict Detection
- **Step 5**：Graph Construction
- **Step 6**：Rule-based Graph Retrieval
- **Step 7（当前新增）**：Answer Generation

当前实现聚焦在可验证的中间层：
- 数据 schema（Pydantic）
- JSONL 读写与加载
- 跨文件一致性校验
- Mock LLM 抽取框架（可替换）
- Rule-based event merge（deterministic MVP）
- Rule-based conflict detection（deterministic MVP）
- 可复现的 sample 数据与测试

> 当前阶段**不包含**真实 LLM API 调用、完整 GraphRAG 编排、最终问答、前端与数据库。

## Step 4: Claim Conflict Detection
- 使用正式 `events` 和 `claims`
- 按 `event_id + topic` 分组 claims
- 生成候选冲突组（同组至少两个不同 claimant）
- 使用 rule-based MVP 判断冲突
- 当前不使用真实 LLM
- 当前输出所有候选结果（包括 `is_conflict=false`）方便 debug
- 后续可以替换为 LLM judge

## Step 5: Graph Construction
- 输入：`chunks/events/claims/conflicts`
- 输出：`data/graph/nodes.jsonl` 与 `data/graph/edges.jsonl`
- 规则：构建 event/claim/chunk/actor/location/conflict 节点及关系边
- 当前仅文件化图结构，不接 Neo4j，不做检索与问答

## Step 6: Rule-based Graph Retrieval
- 当前实现：rule-based retriever
- 不使用 embedding
- 不使用 Neo4j
- 不使用 LLM
- 输出 retrieval context 供人工检查与后续 answer generation 使用

运行示例：
```bash
python scripts/retrieve_sample.py "What claims conflict about the target?"
python scripts/retrieve_sample.py "How did oil prices respond?"
python scripts/retrieve_sample.py "What happened near Isfahan?"
```

## Step 7: Answer Generation
- 基于 Step 6 retrieval context 进行结构化回答生成
- 当前为 deterministic 模板化答案，不接入真实 LLM
- 回答包含：Conclusion / Key Events / Claims by Actor / Conflicts and Uncertainty / Evidence / Limitations

运行示例：
```bash
python scripts/answer_sample.py "What claims conflict about the target?"
python scripts/answer_sample.py "How did oil prices respond?"
python scripts/answer_sample.py "What happened near Isfahan?"
```


## Run the full MVP sample pipeline
```bash
python scripts/run_mvp_sample.py
```

说明：
- 该脚本会覆盖 `data/processed` 和 `data/graph` 下的 sample 输出。
- 全流程只使用 MockLLM / rule-based modules。
- 不调用真实 LLM。
- 不需要 Neo4j。
- 不需要向量数据库。


## Step 9: Evaluation Runner
运行方式：
```bash
python scripts/run_mvp_sample.py
python scripts/run_eval_sample.py
```

说明：
- 当前评估是 keyword-based lightweight evaluation。
- 不使用真实 LLM judge。
- 目标是检查 retrieval 和 answer generation 是否命中预期信息。
- 后续可以扩展为人工评分或 LLM-as-judge。

## 核心对象
- **Event**：发生了什么（canonical）
- **Claim**：谁如何描述这件事（canonical）
- **Conflict**：同一事件下 claim 之间是否冲突
- **Chunk**：证据来自哪里
- **TempEvent / TempClaim**：按 chunk 抽取的临时中间结果


## Project Docs
- `AGENTS.md`：给 Codex 的长期开发规则（开发约束、测试要求、禁做事项）。
- `PROJECT_SPEC.md`：项目设计与 pipeline 说明（目标、schema、步骤、JSONL 约定）。
- `PROMPTS.md`：LLM prompt 集合（抽取、共指、canonical 生成、冲突判断、最终回答）。

这些文档用于减少后续任务 prompt 长度；当 schema 或 pipeline 变更时应同步更新。

## 安装依赖
```bash
pip install -r requirements.txt
```

## 推荐运行顺序
```bash
python scripts/validate_sample.py
python scripts/extract_sample.py
python scripts/merge_sample.py
python scripts/validate_processed.py
python scripts/detect_conflicts_sample.py
python scripts/build_graph_sample.py
pytest
```

## 产物
- Step 2:
  - `data/processed/temp_events.jsonl`
  - `data/processed/temp_claims.jsonl`
- Step 3:
  - `data/processed/events.jsonl`
  - `data/processed/claims.jsonl`
  - `data/processed/temp_event_mapping.jsonl`
- Step 4:
  - `data/processed/conflicts.jsonl`

- Step 5:
  - `data/graph/nodes.jsonl`
  - `data/graph/edges.jsonl`
