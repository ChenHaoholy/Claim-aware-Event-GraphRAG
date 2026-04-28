# Claim-aware Event GraphRAG

## 项目目标
本项目用于构建一个“事件（Event）—声明（Claim）—证据片段（Chunk）”图谱问答系统。

## 当前阶段
- **Step 1**：schema + sample data + validation
- **Step 2**：Chunk 级 Event + Claim 抽取（temp_events / temp_claims）
- **Step 3（当前新增）**：Event Merge and Claim Canonicalization

当前实现聚焦在可验证的中间层：
- 数据 schema（Pydantic）
- JSONL 读写与加载
- 跨文件一致性校验
- Mock LLM 抽取框架（可替换）
- Rule-based event merge（deterministic MVP）
- 可复现的 sample 数据与测试

> 当前阶段**不包含**真实 LLM API 调用、GraphRAG 编排、conflict detection、前端与数据库。

## Step 3: Event Merge and Claim Canonicalization
- Step 2 先生成 `temp_events` 和 `temp_claims`
- Step 3 使用 rule-based 方法合并 `temp_events`
- 生成正式 `events` 和 `claims`
- 当前不使用 LLM 判断合并
- 当前规则是 MVP，后续可替换为 embedding + LLM pairwise 判断

## 核心对象
- **Event**：发生了什么（canonical）
- **Claim**：谁如何描述这件事（canonical）
- **Chunk**：证据来自哪里
- **TempEvent / TempClaim**：按 chunk 抽取的临时中间结果

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
