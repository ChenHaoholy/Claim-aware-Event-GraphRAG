# Claim-aware Event GraphRAG

## 项目目标
本项目用于构建一个“事件（Event）—声明（Claim）—证据片段（Chunk）”图谱问答系统。

## 当前阶段
**Step 1：schema + sample data + validation**

当前实现聚焦在可验证的中间层：
- 数据 schema（Pydantic）
- JSONL 读写与加载
- 跨文件一致性校验
- 可复现的 sample 数据与测试

> 本阶段**不包含** LLM 调用、GraphRAG 编排、前端与数据库。

## 三个核心对象
- **Event**：发生了什么
- **Claim**：谁如何描述这件事
- **Chunk**：证据来自哪里

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行样例数据验证
```bash
python scripts/validate_sample.py
```

## 运行测试
```bash
pytest
```
