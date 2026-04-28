# Claim-aware Event GraphRAG

## 项目目标
本项目用于构建一个“事件（Event）—声明（Claim）—证据片段（Chunk）”图谱问答系统。

## 当前阶段
- **Step 1**：schema + sample data + validation
- **Step 2（当前新增）**：Chunk 级 Event + Claim 抽取（temp_events / temp_claims）

当前实现聚焦在可验证的中间层：
- 数据 schema（Pydantic）
- JSONL 读写与加载
- 跨文件一致性校验
- Mock LLM 抽取框架（可替换）
- 可复现的 sample 数据与测试

> 当前阶段**不包含**真实 LLM API 调用、GraphRAG 编排、event merge、conflict detection、前端与数据库。

## 核心对象
- **Event**：发生了什么
- **Claim**：谁如何描述这件事
- **Chunk**：证据来自哪里
- **TempEvent / TempClaim**：按 chunk 抽取的临时中间结果

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行样例数据验证（Step 1）
```bash
python scripts/validate_sample.py
```

## 运行样例抽取（Step 2）
```bash
python scripts/extract_sample.py
```

会生成：
- `data/processed/temp_events.jsonl`
- `data/processed/temp_claims.jsonl`

## 运行测试
```bash
pytest
```
