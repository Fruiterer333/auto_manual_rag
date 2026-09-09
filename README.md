# Auto Manual RAG

面向汽车用户手册的本地 RAG 问答系统。项目从 PDF 中恢复手册层级结构，通过 Dense + BM25 + RRF 混合检索组织证据，再由本地模型生成回答并返回页码、章节和原文摘录。

系统覆盖结构感知解析、Evidence-grounded Answering、引用溯源、FastAPI/Streamlit/CLI 入口，以及 retrieval/answer evaluation。

## Demo

![Auto Manual RAG Streamlit demo](docs/assets/demo.png)

> **问题：** 自动驻车 Auto Hold 的作用是什么？
>
> **回答：** 系统会在正常驾驶中的短暂停车时自动提供制动，驾驶员无需持续踩住制动踏板；需要起步时可踩下加速踏板，或用力踩下制动踏板后松开。
>
> **引用：** 用户手册第 159 页，`启动和驾驶 > 自动驻车系统`。

## Features

- **Manual-aware parsing**：恢复 `chapter`、`section`、`subsection` 和 `heading_path`，保留页码、风险等级和跨页信息。
- **Hybrid retrieval**：组合 Chroma dense retrieval 与 BM25 sparse retrieval，并使用 RRF 融合两路排名。
- **Optional reranking**：支持本地 cross-encoder reranker，默认关闭，可用于更强调 top-1 精度的场景。
- **Evidence hygiene**：过滤目录和低信息噪声，执行精确内容去重，并保留可解释的诊断 metadata。
- **Evidence-grounded answering**：最终上下文限制为最多 5 条、6000 字符，由 Ollama `qwen3.5:9b` 基于明确 Evidence 回答。
- **Traceable evaluation**：提供 retrieval/answer datasets、benchmark consistency validation、Exact Prompt Evidence 和结构化 citations。

## Architecture

```mermaid
flowchart TD
    A[Automotive Manual PDF] --> B[PDF Loader and Cleaner]
    B --> C[Manual-aware Parser]
    C --> D[Structured Chunks]
    D --> E[Chroma Dense Index]
    D --> F[BM25 Sparse Index]
    E --> G[RRF Hybrid Retrieval]
    F --> G
    G --> H[Filter and Dedup]
    H -. optional .-> I[Cross-Encoder Rerank]
    H --> J[Context Selection]
    I --> J
    J --> K[Grounded Evidence Prompt]
    K --> L[Ollama qwen3.5:9b]
    L --> M[Answer and Citations]
```

默认链路使用 hybrid retrieval，不启用 reranker。

## Quick Start

### Prerequisites

- Git
- Python 3.10+
- [Ollama](https://ollama.com/)
- 首次下载 embedding/LLM 模型时可访问对应模型源

### 1. Clone and install

```bash
git clone https://github.com/Fruiterer333/auto_manual_rag.git
cd auto_manual_rag
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1` 激活环境。

### 2. Prepare Ollama

```bash
ollama serve
```

在另一个终端执行：

```bash
ollama pull qwen3.5:9b
```

默认 generation configuration 为 `temperature=0.0`、`seed=42`、`stream=false`、`think=false`。

### 3. Configure

```bash
cp .env.example .env
```

### 4. Build indexes from the included manual

仓库包含用于 Demo 和评测复现的手册：`data/manuals/demo_manual.pdf`。

```bash
.venv/bin/python scripts/ingest_manual.py \
  --file-path data/manuals/demo_manual.pdf \
  --rebuild
```

该命令构建 Chroma dense index 和 BM25 sparse index。本地索引保存在忽略目录中，不提交 Git。

### 5. Ask a question

```bash
.venv/bin/python scripts/query_manual.py \
  --question "自动驻车 Auto Hold 的作用是什么？" \
  --retrieval-mode hybrid
```

## Usage

### CLI

```bash
.venv/bin/python scripts/query_manual.py \
  --question "如何正确使用安全带？" \
  --retrieval-mode hybrid
```

### FastAPI

```bash
.venv/bin/python -m uvicorn app.main:app --reload
curl http://127.0.0.1:8000/health
```

API 文档位于 `http://127.0.0.1:8000/docs`。

### Streamlit

FastAPI 运行后，在另一个终端启动：

```bash
.venv/bin/python -m streamlit run frontend/streamlit_app.py
```

访问 `http://127.0.0.1:8501`。

## Evaluation

检索评测包含 68 条 active queries。以下指标衡量 gold Evidence 的检索排名质量，不是 answer accuracy、system accuracy 或 production accuracy。

| Configuration | Hit@1 | Hit@3 | Hit@5 | MRR |
| --- | ---: | ---: | ---: | ---: |
| Hybrid | 0.6618 | 0.9265 | 0.9706 | 0.7922 |
| Hybrid + Reranker | 0.8676 | 0.9853 | 1.0000 | 0.9277 |

Answer-level evaluation 另外检查 groundedness、correctness、completeness 和 condition handling。评测记录模型实际可见的 Exact Prompt Evidence，用于区分 retrieval failure 与 generation failure。

- [Evaluation methodology](docs/evaluation.md)
- [Final evaluation report](reports/evaluation/README.md)

## Engineering Decisions

| Decision | Rationale |
| --- | --- |
| Dense + BM25 + RRF | Dense 提供语义召回，BM25 保留术语和精确短语匹配；RRF 可以融合不同分数尺度的排名。 |
| Optional reranker | Cross-encoder 将 Hit@1 从 `0.6618` 提升到 `0.8676`，但增加本地推理开销，因此不作为默认链路。 |
| `qwen3.5:9b` | 在 model-visible Evidence 保持一致的本地候选模型比较中选定，兼顾回答质量、模型大小和运行成本。 |
| Exact Prompt Evidence | 保存模型实际看到的证据，使回答、citations 和 evaluation 能基于同一上下文审计。 |

## Limitations

- 当前 benchmark 主要来自单份汽车用户手册，不能代表跨品牌、跨车型效果。
- 系统以文本为主，不覆盖图片、按钮图标、OCR 或复杂表格中的视觉信息。
- Parser 对汽车手册的层级结构存在领域假设，更换文档后需要检查 chunk metadata。
- 当前性能数据来自本地离线实验，没有正式 production p50/p95 latency benchmark。

## Project Structure

```text
app/                    FastAPI、ingest、RAG 和 evaluation 核心代码
frontend/               Streamlit 应用
scripts/                ingest、query、inspection 和 evaluation CLI
tests/                  单元测试
data/manuals/           Demo / evaluation manual
data/eval/              retrieval 与 answer evaluation datasets
docs/                   评测方法和 Demo 资产
reports/evaluation/     最终机器可读结果与必要技术证据
```

## License

项目源代码基于 [MIT License](LICENSE) 发布。仓库内汽车用户手册的版权和商标权归原权利人所有，不包含在 MIT 源代码授权范围内。
