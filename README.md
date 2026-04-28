# Claim-aware Event GraphRAG

## 项目目标
本项目用于构建一个“事件（Event）—声明（Claim）—证据片段（Chunk）”图谱问答系统。

## 当前阶段
- **Step 1**：schema + sample data + validation
- **Step 2**：Chunk 级 Event + Claim 抽取（temp_events / temp_claims）
- **Step 3**：Event Merge and Claim Canonicalization
- **Step 4（当前新增）**：Claim Conflict Detection

当前实现聚焦在可验证的中间层：
- 数据 schema（Pydantic）
- JSONL 读写与加载
- 跨文件一致性校验
- Mock LLM 抽取框架（可替换）
- Rule-based event merge（deterministic MVP）
- Rule-based conflict detection（deterministic MVP）
- 可复现的 sample 数据与测试

> 当前阶段**不包含**真实 LLM API 调用、GraphRAG 编排、检索、最终问答、前端与数据库。

## Step 4: Claim Conflict Detection
- 使用正式 `events` 和 `claims`
- 按 `event_id + topic` 分组 claims
- 生成候选冲突组（同组至少两个不同 claimant）
- 使用 rule-based MVP 判断冲突
- 当前不使用真实 LLM
- 当前输出所有候选结果（包括 `is_conflict=false`）方便 debug
- 后续可以替换为 LLM judge

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
