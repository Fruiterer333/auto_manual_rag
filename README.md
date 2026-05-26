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

日志配置：

```env
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

`LOG_LEVEL` 控制日志详细程度。`LOG_FILE` 为空时只输出到控制台；设置 `LOG_FILE` 后会同时写入文件，并自动创建父目录。推荐本地调试使用 `INFO`；如果需要更详细的检索细节，例如检索结果文本 preview，可以设置 `LOG_LEVEL=DEBUG`。

验证文件日志：

```bash
python -c "from app.core.logger import get_logger; logger=get_logger('test_logger'); logger.info('hello log file test')"
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

## V1.1 检索调试

普通问答：

```bash
python scripts/query_manual.py --question "如何正确使用安全带？"
```

检索调试：

```bash
python scripts/query_manual.py --question "车辆涉水驾驶后需要检查什么？" --debug-retrieval
```

`--debug-retrieval` 模式不会调用 Ollama，只用于查看 Chroma 检索结果。

V1.1.1 中 debug retrieval 会显示 `score` 和 `distance`：

- `distance` 越小越相关。
- `score` 越高越相关。
- 当前 `score = 1 - distance`，基于 Chroma cosine distance。

查看完整 chunk：

```bash
python scripts/query_manual.py --question "车辆涉水驾驶后需要检查什么？" --debug-retrieval --show-full-chunk
```

当前 Chroma collection 显式使用 cosine metric。如果更新后发现 score/distance 行为异常，或者旧 collection 不是 cosine，请重新构建索引：

```bash
python scripts/ingest_manual.py --rebuild
```

## V2.0 Manual-Aware Chunk

V2.0 引入汽车用户手册结构化解析和 manual-aware chunk。索引构建时会先从 PDF 页文本中解析基础手册结构，再生成更细粒度、更适合检索的 chunk。

新的 chunk 会尽量保留：

- `chapter`
- `section`
- `warning` / `caution` / `note`
- `procedure`
- `risk_level`

重新构建索引：

```bash
python scripts/ingest_manual.py --rebuild
```

查看结构化检索结果：

```bash
python scripts/query_manual.py --question "如何正确使用安全带？" --debug-retrieval
```

V2.0 仍然没有实现 hybrid search、rerank、query rewrite 或评估体系，这些属于后续版本。

## V2.1 Parser 校准与 Context Selection

V2.1 校准了 manual parser 规则，减少正文长句被误判为 section，并收紧 `warning`、`procedure` 和 `risk_level` 的规则。V2.1 还增加了可关闭的轻量 metadata-aware context selection：不做额外检索，不引入新模型，只在 Chroma 已召回的候选结果内部，根据 section/chapter/content_type/risk_level/text 关键词做小幅排序加权。

配置项：

```env
ENABLE_METADATA_CONTEXT_SELECTION=true
CONTEXT_SELECTION_CANDIDATE_K=10
```

普通 query 默认使用 context selection。debug retrieval 默认查看原始 Chroma 排序：

```bash
python scripts/query_manual.py --question "充电时有哪些安全注意事项？" --debug-retrieval
```

查看 selection 后排序：

```bash
python scripts/query_manual.py --question "充电时有哪些安全注意事项？" --debug-retrieval --use-context-selection
```

V2.1 仍然没有实现 hybrid search、BM25、cross-encoder rerank 或评估体系，这些属于后续 V3。

## V2.2 上下文质量修复

V2.2 修复了 V2 相比 V1 的上下文质量退化问题：

- 进一步收紧 section 识别，减少正文、图标说明、警告灯说明被误判为 section。
- 新增 query-time dedup，减少重复 chunk 进入 prompt 和 citations。
- 新增 neighbor context expansion，用于补全跨页或相邻的 warning/caution/procedure 内容。
- 对最终回答做轻量 post-process，移除“资料4 / 片段1 / 上下文2”等内部上下文编号表达。

新增配置项：

```env
ENABLE_NEIGHBOR_CONTEXT_EXPANSION=true
MAX_CONTEXT_CHARS=6000
NEIGHBOR_EXPANSION_MAX_PER_CHUNK=1
```

V2.2 仍未实现 hybrid search、BM25、cross-encoder rerank，这些属于 V3。

验收命令：

```bash
python scripts/ingest_manual.py --rebuild
python scripts/query_manual.py --question "如何正确使用安全带？" --debug-retrieval --use-context-selection
python scripts/query_manual.py --question "充电时有哪些安全注意事项？" --debug-retrieval --use-context-selection
python scripts/query_manual.py --question "充电时有哪些安全注意事项？"
```

## V2.3 Cleanup / Stabilize

V2.3 是 cleanup/stabilize 版本。V2.2 中尝试的 neighbor context expansion 在实验中会引入弱相关上下文，因此默认关闭。V2.3 保留确实有效的 prompt 防内部编号泄漏修复，保留轻量 metadata-aware context selection，并将 dedup 简化为安全清理。

推荐配置：

```env
ENABLE_METADATA_CONTEXT_SELECTION=true
CONTEXT_SELECTION_CANDIDATE_K=10
ENABLE_NEIGHBOR_CONTEXT_EXPANSION=false
MAX_CONTEXT_CHARS=6000
NEIGHBOR_EXPANSION_MAX_PER_CHUNK=1
```

V2.3 不再继续堆规则修安全带/充电问题。剩余问题，例如“安全带操作问题无法稳定优先命中最相关 chunk”“充电相关多义词导致弱相关召回”，交给 V3 的 hybrid retrieval / BM25 / rerank 处理。

测试命令：

```bash
python scripts/query_manual.py --question "如何正确使用安全带？" --debug-retrieval --use-context-selection
python scripts/query_manual.py --question "胎压报警后应该怎么办？"
python scripts/query_manual.py --question "充电时有哪些安全注意事项？" --debug-retrieval --use-context-selection
python scripts/query_manual.py --question "车辆涉水驾驶后需要检查什么？"
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
