# Auto Manual RAG Assistant

Auto Manual RAG Assistant 是一个面向汽车用户手册的本地化 RAG 问答系统项目。项目目标是基于汽车用户产品手册 PDF，逐步构建支持文档解析、结构化 chunk、向量检索、本地大模型问答、引用溯源、前端展示和评估体系的智能用车助手。

当前版本是 V1 最小 RAG 闭环版本，支持 PDF 文本抽取、基础清洗、fixed-size chunk、本地 embedding、Chroma 入库、检索、Ollama 回答和引用返回。

## 项目规范

本项目包含 `AGENTS.md`。后续使用 Codex 或其他 AI coding agent 修改代码前，应先阅读并遵守 `AGENTS.md` 中的项目规范，避免跨版本实现、硬编码配置或破坏既有目录结构。

## 目录结构

```text
app/        FastAPI 后端、配置、数据处理和 RAG 模块
frontend/   Streamlit 前端占位页面
data/       原始文档、处理中间结果和本地 Chroma 数据目录
scripts/    命令行脚本
tests/      测试代码
```

## 安装依赖

建议使用 Python 3.10+。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如需自定义配置：

```bash
cp .env.example .env
```

## V1 使用流程

准备 PDF：

```bash
mkdir -p data/raw
cp /path/to/your/manual.pdf data/raw/train_a.pdf
```

安装并启动 Ollama：

```bash
ollama pull qwen2.5:7b
ollama serve
```

构建索引：

```bash
python scripts/ingest_manual.py --rebuild
```

命令行提问：

```bash
python scripts/query_manual.py --question "如何正确使用安全带？"
```

## 启动 FastAPI

```bash
uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 启动 Streamlit

```bash
streamlit run frontend/streamlit_app.py
```

## 版本路线

- V1：最小 RAG 闭环
- V2：汽车手册结构化解析
- V3：检索优化
- V4：安全回答策略
- V5：评估体系
- V6：前端展示和工程化

## Git 提交建议

```bash
git add .
git commit -m "init project skeleton"
```
