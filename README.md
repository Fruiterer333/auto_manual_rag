# Auto Manual RAG

`auto-manual-rag` 是一个基于汽车用户手册的本地化 RAG 问答系统。系统从汽车用户手册 PDF 中抽取和组织文本，通过检索定位相关片段，再由本地大模型基于引用证据生成回答。

项目目标不是实现一个最小问答 demo，而是构建一条可复现、可评测、可诊断、可迭代的垂直领域 RAG 工程链路。当前项目已经支持 hybrid retrieval、metadata-aware context selection、retrieval evaluation、cross-mode diagnostics 和可选的 cross-encoder rerank。

## 1. 项目简介

汽车用户手册包含车辆功能、报警处理、安全提示、维护保养、参数限制等内容。普通文档问答可以完成基础检索，但容易受到目录残片、泛化说明、相近章节和关键词多义性的干扰。

本项目围绕这些实际问题逐步实现：

- 汽车用户手册 PDF 解析与结构化切分；
- dense retrieval 与 BM25 sparse retrieval；
- 基于 RRF 的 hybrid retrieval；
- TOC/noise filtering 和 content-level dedup；
- metadata-aware context selection；
- 带引用来源的本地模型回答；
- retrieval evaluation framework；
- dense / BM25 / hybrid 的 cross-mode diagnostics；
- 可关闭的本地 CrossEncoderReranker；
- rerank on/off evaluation comparison。

本项目包含 [`AGENTS.md`](AGENTS.md)。使用 Codex、Claude Code 或其他 AI coding agent 修改代码前，应先阅读并遵守其中的架构边界、反过拟合原则和评测驱动约束。

## 2. 项目目标

- 构建一个可复现、可评测、可迭代的垂直领域 RAG 系统。
- 面向汽车用户手册场景，支持车辆功能、操作步骤、安全提示、报警处理和维护检查等问题。
- 通过 evaluation dataset 和自动化报告比较检索方案，避免围绕少量 smoke tests 过拟合。
- 保持模块职责清晰，使 ingest、retrieval、context selection、generation 和 evaluation 可以独立诊断。
- 形成适合简历展示和面试讲解的 RAG 工程项目。

## 3. 核心功能

- PDF 文档 ingest；
- manual-aware chunking；
- 本地 embedding；
- Chroma dense retrieval；
- BM25 sparse retrieval；
- dense + BM25 + RRF hybrid retrieval；
- TOC/noise hygiene filtering；
- content-level dedup；
- metadata-aware context selection；
- citation-aware answer generation；
- Ollama 本地大模型调用；
- `inspect_chunks.py` 索引诊断；
- retrieval evaluation；
- cross-mode diagnostics；
- 本地 cross-encoder rerank；
- rerank on/off JSON 对比报告；
- FastAPI 后端和 Streamlit 前端。

## 4. 系统架构

```text
User Query
  -> Query Processing
  -> Dense / BM25 / Hybrid Retrieval
  -> Hygiene Filter / Dedup
  -> Optional Cross-Encoder Rerank
  -> Context Selection
  -> Prompt Construction
  -> Local LLM Answer with Citations
```

模块职责：

- **Retrieval**：从索引中召回候选 chunk。支持 `dense`、`bm25` 和 `hybrid` 三种模式。
- **Hygiene Filter / Dedup**：过滤目录、噪声和重复内容，减少无效上下文。
- **Optional Cross-Encoder Rerank**：对 query-chunk pair 做精排。默认关闭，可通过配置或评测 CLI 显式启用。
- **Context Selection**：整理最终上下文、控制长度、保留 metadata 和引用来源。
- **Generation**：构造 prompt，并通过 Ollama 调用本地模型生成回答。
- **Evaluation**：使用结构化 dev set 和可复现指标比较不同检索与排序方案。

`context selection` 不是 reranker。它只负责在候选上下文中做保守整理，不能替代检索或精排。

## 5. 当前版本进展

| Version | Module | Summary |
| --- | --- | --- |
| V1 | Minimal RAG | 完成 PDF ingest、向量检索、本地模型回答和引用返回。 |
| V2 | Manual-aware chunking | 针对汽车手册结构优化 chunking、metadata 和 context selection。 |
| V3.0 | Hybrid retrieval | 引入 BM25，并通过 RRF 与 dense retrieval 融合。 |
| V3.0.1 | Index hygiene | 增加 TOC/noise filtering、content-level dedup 和 chunk inspection。 |
| V3.0.2 | Retrieval evaluation | 建立 `manual_eval_set.jsonl`、检索指标和评测 runner。 |
| V3.0.3 | Retrieval diagnostics | 增加 cross-mode case comparison 和 regression 诊断。 |
| V3.1.0 | Reranker interface | 增加 `BaseReranker`、`NoopReranker` 和 pipeline hook。 |
| V3.1.1 | Cross-Encoder rerank | 接入本地 `CrossEncoderReranker` baseline。 |
| V3.1.2 | Rerank comparison | 增加 rerank on/off JSON 对比报告。 |
| V3.2 | Eval set cleanup and rerank review | 将评测集扩展并清洗为 69 条 text-only dev cases，复核 rerank 收益与延迟成本。 |

## 6. 评测体系

评测体系用于指导迭代，不是装饰性脚本。当前评测集位于：

```text
data/eval/manual_eval_set.jsonl
```

每条 eval case 包含问题、类别、意图、期望页码、可接受章节、关键词和来自真实手册 chunk 的 evidence。当前数据集是 dev set，不是最终 benchmark。

核心指标：

- `evidence_hit@1` / `evidence_hit@3` / `evidence_hit@5`
- `MRR`
- `average_first_hit_rank`
- `page_hit@k`
- `term_coverage_ratio@k`
- `noise_rate@k`
- `duplicate_chunk_id_rate@k`
- `same_page_duplicate_rate@k`
- `cross_page_repeated_content_rate@k`
- `final_context_hit`

指标解读：

- `evidence_hit@5` 用于观察候选召回是否成功。
- `evidence_hit@1` 和 `MRR` 更适合观察排序质量。
- `section_hit` 依赖 parser metadata 质量，应结合 page、evidence 和 term coverage 解读。
- smoke tests 只用于发现明显回归，不能替代完整 dev set。
- 单个 eval case 的失败不足以证明应该新增检索规则。

更完整的评测说明见 [`docs/evaluation.md`](docs/evaluation.md)。

## 7. Rerank 阶段结果

V3.2 使用清洗后的 text-only dev set 对比了 hybrid retrieval 在关闭和启用 cross-encoder rerank 时的表现：

- eval set：`manual_eval_set.jsonl`
- case count：69
- retrieval mode：`hybrid`
- rerank model：`BAAI/bge-reranker-base`
- `top_k`：5

在当前 69 条 text-only dev evaluation set 上，hybrid + cross-encoder rerank 将 evidence_hit@1 从 0.7681 提升到 0.9130，将 MRR 从 0.8792 提升到 0.9541，同时 evidence_hit@5 保持 1.0000。

| Metric | Hybrid no rerank | Hybrid + rerank | Delta |
| --- | ---: | ---: | ---: |
| `evidence_hit@1` | 0.7681 | 0.9130 | +0.1449 |
| `MRR` | 0.8792 | 0.9541 | +0.0749 |
| `evidence_hit@5` | 1.0000 | 1.0000 | +0.0000 |
| `elapsed_seconds` | 23.7179 | 42.8940 | +19.1761 |
| `average_seconds_per_case` | 0.3437 | 0.6217 | +0.2780 |

Case movement：

| Item | Count |
| --- | ---: |
| `improved_cases` | 11 |
| `regressed_cases` | 1 |
| `unchanged_cases` | 57 |
| `newly_top1_hit` | 10 |
| `lost_top1_hit` | 0 |
| `evidence_hit@5_regressions` | 0 |

当前结论：

- rerank 在当前 dev set 上改善了 top-1 排序；
- rerank 没有破坏 top-5 evidence recall；
- rerank 增加了推理耗时；
- rerank 仍应作为 optional precision-ranking module；
- 当前评测仍是单一手册 dev set，且 rerank 带来约 1.81x latency cost，因此不应默认开启。

默认配置保持：

```env
ENABLE_RERANK=false
```

## 8. 安装与运行

### 8.1 创建虚拟环境

建议使用 Python 3.10+：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 8.2 准备 PDF

```bash
mkdir -p data/raw
cp /path/to/your/manual.pdf data/raw/train_a.pdf
```

### 8.3 安装并启动 Ollama

```bash
ollama pull qwen2.5:7b
ollama serve
```

### 8.4 构建索引

```bash
.venv/bin/python scripts/ingest_manual.py --rebuild
```

构建过程会写入 Chroma dense index 和 BM25 index。修改 chunking、filtering、tokenizer 或 indexing 逻辑后，需要重新构建索引。

### 8.5 命令行提问

```bash
.venv/bin/python scripts/query_manual.py \
  --question "如何正确使用安全带？" \
  --retrieval-mode hybrid
```

### 8.6 检索调试

```bash
.venv/bin/python scripts/query_manual.py \
  --question "充电时有哪些安全注意事项？" \
  --debug-retrieval \
  --retrieval-mode hybrid \
  --use-context-selection
```

查看完整 chunk：

```bash
.venv/bin/python scripts/query_manual.py \
  --question "车辆涉水驾驶后需要检查什么？" \
  --debug-retrieval \
  --retrieval-mode hybrid \
  --show-full-chunk
```

检查 BM25 index 中的 chunks：

```bash
.venv/bin/python scripts/inspect_chunks.py --page-range 99 103 --show-full
```

### 8.7 启动 FastAPI

```bash
uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

### 8.8 启动 Streamlit

```bash
streamlit run frontend/streamlit_app.py
```

## 9. Evaluation 命令

### 9.1 Dense / BM25 / Hybrid 对比

```bash
.venv/bin/python scripts/evaluate_retrieval.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --all-modes \
  --top-k 5 \
  --output /tmp/v3_all_modes.md \
  --output-format md
```

### 9.2 Hybrid baseline

```bash
.venv/bin/python scripts/evaluate_retrieval.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --retrieval-mode hybrid \
  --top-k 5 \
  --output /tmp/v3_2_hybrid_no_rerank.json \
  --output-format json
```

### 9.3 Hybrid + rerank

```bash
.venv/bin/python scripts/evaluate_retrieval.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --retrieval-mode hybrid \
  --top-k 5 \
  --enable-rerank \
  --rerank-device cpu \
  --output /tmp/v3_2_hybrid_rerank.json \
  --output-format json
```

首次启用 rerank 时，`sentence-transformers` 可能需要下载 `BAAI/bge-reranker-base`。默认查询链路不会加载 reranker 模型。

### 9.4 Rerank on/off 对比

```bash
.venv/bin/python scripts/compare_rerank_evaluation.py \
  --baseline /tmp/v3_2_hybrid_no_rerank.json \
  --experiment /tmp/v3_2_hybrid_rerank.json \
  --output reports/evaluation/v3_2_rerank_comparison.md \
  --output-format md
```

`reports/evaluation/` 下的运行产物默认不建议直接提交。需要保留阶段结论时，应整理为 `docs/` 下的总结文档。

## 10. 配置说明

常用配置位于 `.env`：

```env
LOG_LEVEL=INFO
LOG_FILE=
RETRIEVAL_MODE=hybrid
ENABLE_METADATA_CONTEXT_SELECTION=true
ENABLE_NEIGHBOR_CONTEXT_EXPANSION=false
ENABLE_RERANK=false
RERANK_MODEL_NAME=BAAI/bge-reranker-base
RERANK_TOP_N=10
RERANK_OUTPUT_TOP_K=5
RERANK_DEVICE=auto
```

日志说明：

- `LOG_LEVEL` 控制日志详细程度。
- `LOG_FILE` 为空时只输出到控制台。
- 设置 `LOG_FILE=logs/app.log` 后会同时写入文件，并自动创建父目录。
- 本地调试推荐使用 `INFO`；查看更详细检索信息时可以使用 `DEBUG`。

验证文件日志：

```bash
.venv/bin/python -c "from app.core.logger import get_logger; logger=get_logger('test_logger'); logger.info('hello log file test')"
```

## 11. 项目文档

- [评测体系说明](docs/evaluation.md)
- [Rerank 设计文档](docs/rerank_design.md)
- [Rerank evaluation summary](docs/evaluation/rerank_evaluation_summary.md)

## 12. 当前限制

- 当前 eval set 包含 69 条 text-only dev cases，结果来自单一手册 dev set，不是 final benchmark。
- rerank 仍默认关闭，没有比较多个 reranker 模型。
- latency 目前以整体运行时间和平均每 case 时间观察，还需要继续统计和优化。
- 部分 section metadata 仍然缺失或存在解析偏差。
- 仍有少数 case 未被 rerank 解决，例如部分非 top-1 操作题和警告题。
- 当前项目是纯文本 RAG，不处理依赖图片、图标或 OCR 的问题。
- 后续仅在增加覆盖面时继续扩充 text-only dev cases，并结合更广泛评测和 latency review 决定 rerank 的默认策略。

## 13. Roadmap

- 仅在增加覆盖面时继续扩充 text-only dev cases。
- 增强 rerank latency 统计，评估 batch、device 和 `max_length` 的影响。
- Review remaining non-top1 cases，区分 retrieval、metadata 和 chunk quality 问题。
- 在更大 dev set 上比较不同 reranker 模型。
- 改进 metadata quality。
- 完善 FastAPI、Streamlit 和本地部署体验。
- 整理最终简历版项目说明和面试讲解材料。

## 14. Git 提交注意事项

提交前建议运行：

```bash
git diff --check
git status
```

不要提交：

- `.env`
- `data/raw/`
- `data/chroma/`
- `data/processed/*.pkl`
- `logs/`
- 模型缓存
- `/tmp` 下的运行产物
- 未经整理的 `reports/evaluation/` 运行报告
