# Auto Manual RAG 冻结技术事实

本文档是 V5.0-C Resume / Interview / Release Package 的事实基线。简历、面试和发布材料中的技术描述应与本页及其引用的代码、配置、冻结报告一致。

## 项目定位

- 应用：Auto Manual RAG
- 场景：面向汽车用户手册的本地、可追溯知识问答
- 目标岗位：AI Application Engineer；兼容 LLM Application Engineer、RAG Engineer、AI Backend Engineer
- 边界：single-manual、text-only；不是 Agent、GraphRAG、通用文档平台或汽车控制系统
- 用户价值：把非结构化手册转为可检索证据，基于证据生成中文回答，并返回页码、章节与摘录

## 稳定架构

```text
PDF manual
-> PDF loading and cleaning
-> manual-aware hierarchical parser
-> structured chunks and metadata
-> Chroma dense index + BM25 sparse index
-> RRF hybrid retrieval
-> TOC/noise filtering + exact content dedup
-> metadata-aware context selection
-> bounded Evidence prompt
-> Ollama / qwen3.5:9b
-> answer + structured citations
```

## 数据与 Chunk

| 项目 | 当前实现 |
| --- | --- |
| Parser | `ManualStructureParser` |
| Splitter | `ManualStructureSplitter`，空结果时保留 fixed splitter fallback |
| Hierarchy | `chapter`、`section`、`subsection` |
| Heading path | `ManualBlock.heading_path`；最终 `Chunk` 中保存在 metadata |
| Chunk metadata | page、chapter、section、subsection、heading_path、content_type、risk_level、source_pages、chunk_index 等 |
| Heading text policy | section 作为 metadata，不重复写入正文；subsection 会 prepend 到 block/chunk text，增强小节语义 |
| Safety labels | warning、caution、note、procedure 的分类与风险 metadata |

## 检索与上下文

| 字段 | 稳定值或实现 |
| --- | --- |
| Embedding | `BAAI/bge-small-zh-v1.5` |
| Dense store | Chroma |
| Sparse retrieval | `rank-bm25` / BM25Okapi |
| Fusion | Reciprocal Rank Fusion，`RRF_K=60` |
| Retrieval mode | `hybrid` |
| Dense candidate count | 10 |
| Sparse candidate count | 10 |
| Fusion candidate count | 10 |
| User-facing top_k | 5 |
| Rerank | 默认关闭；`BAAI/bge-reranker-base` 作为可选能力 |
| Metadata context selection | 开启 |
| Neighbor expansion | 关闭 |
| Final Evidence count | 最多 5 条 |
| Final Evidence content budget | 最多 6000 字符 |

## 回答生成

| 字段 | 稳定值 |
| --- | --- |
| Runtime | Ollama |
| Model | `qwen3.5:9b` |
| Model digest | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` |
| Quantization / local size | Q4_K_M / 约 6.6 GB |
| Ollama version in frozen evaluation | `0.33.2` |
| Temperature | `0.0` |
| Seed | `42` |
| Stream | `false` |
| Think | `false` |
| Timeout | 120 秒 |
| Prompt | 最多 5 条带 E1-E5 内部标识的 Evidence；标识不得出现在用户回答中 |
| Trace | 记录 Exact Prompt Evidence、raw answer、final answer 和 citations |

`temperature=0` 与固定 seed 只在已记录的当前 Ollama、模型 digest、运行后端和硬件环境中验证了重复运行稳定性，不代表跨机器或跨版本的 bit-for-bit determinism。

## 技术栈

| 层 | 技术 |
| --- | --- |
| Backend / schema | Python、FastAPI、Pydantic、pydantic-settings |
| Data processing | PyMuPDF、自定义 manual-aware parser/splitter |
| Retrieval | Chroma、`BAAI/bge-small-zh-v1.5`、BM25、RRF |
| Optional ranking | sentence-transformers、`BAAI/bge-reranker-base` |
| Generation | Ollama、`qwen3.5:9b` |
| UI / clients | Streamlit、CLI、Requests |
| Evaluation / quality | JSONL datasets、自定义 retrieval/answer evaluator、pytest |

项目没有使用 LangChain、LlamaIndex、Docker、Redis、Kafka、Agent、MCP 或 GraphRAG。

## 冻结评测事实

### Retrieval

- Dataset：69 records，68 active，1 excluded，99 gold evidence。
- Excluded case 表示当前 text-only corpus 无法表示所需表格数值，不进入分母。
- Multi-gold 使用 ANY_OF：命中任一 independently sufficient gold 即成功；MRR 使用排名最高的 gold。
- 当前稳定配置：hybrid、no-rerank、top_k=5。

| Metric | Stable hybrid no-rerank |
| --- | ---: |
| Hit@1 | 0.6618 |
| Hit@3 | 0.9265 |
| Hit@5 | 0.9706 |
| MRR | 0.7922 |

可选 reranker 在同一 dev benchmark 上达到 Hit@1 0.8676、Hit@5 1.0000、MRR 0.9277，但单次离线 elapsed 从约 21.11 秒增加到约 42.96 秒。该 elapsed 不是正式 online latency 或 p95，因此稳定默认仍为 no-rerank。

### Answer

- Dataset：12-case、single-manual answer dev diagnostic set。
- Evaluation semantics：`v4.3`。
- V4.8 结果仍是 **PROPOSED** human rubric review，不是 final external human benchmark。
- PROPOSED：Full Pass 10/12、Severe Failure 1/12、Unsupported Claim 1/12、Critical Safety Omission 1/12。
- 不得把 `10/12` 写成 83.3% accuracy、production accuracy 或跨车型能力。

### Reproducibility and model selection

- `qwen3.5:9b` 在当前固定环境完成 4 cases x 3 runs；Prompt Evidence identity/order/text、raw answer、final answer 均 exact match。
- 三模型受控比较中，`qwen2.5:7b`、`qwen3.5:9b`、`gemma3:12b` 对 12/12 cases 使用完全相同的 Prompt Evidence。
- `qwen3.5:9b` 与 `gemma3:12b` 均改善两个高置信 condition-handling targets；前者约 6.6 GB、平均离线 elapsed 约 15.60 秒，后者约 8.1 GB、约 17.99 秒，因此选择前者。
- elapsed 包含本地离线检索与生成，只能用于同一受控实验内的成本观察。

## 安全 Claim 边界

可用：

- “在 68 条 active retrieval dev queries 上，稳定 hybrid no-rerank 达到 Hit@5 0.9706、MRR 0.7922。”
- “建立 chunk-level retrieval benchmark、answer diagnostic set、Exact Prompt Evidence trace 和人工 rubric。”
- “在 Prompt Evidence 12/12 invariant 的三模型受控比较中选择 `qwen3.5:9b`。”

不可用：

- “系统准确率达到 97%。”
- “回答准确率达到 83.3%。”
- “生产级 RAG”“零幻觉”“跨车型通用”“完全可复现”。
- “rerank 将线上延迟翻倍”，因为现有 elapsed 不是正式线上 latency benchmark。

## 已知限制

- 只验证单本手册；没有跨品牌、跨车型外部 test set。
- text-only pipeline 不处理图片、图标、OCR 和复杂表格布局。
- Answer diagnostic set 只有 12 条，且逐 case 评分仍是 PROPOSED。
- complementary evidence 和 safety-critical evidence 可能无法进入最终上下文。
- 没有完成带 warmup、重复运行和 p50/p95 的正式 latency benchmark。
- fresh clone 的命令已核对，但没有在全新机器上完整下载模型、提供合法手册并重建冻结索引。
- 本地重复运行稳定性不等于跨硬件、跨 Ollama 版本或跨 backend 可复现。

## 事实来源

- 实现：`app/core/config.py`、`app/services/ingest_service.py`、`app/data/parsers/manual_structure_parser.py`、`app/rag/`。
- Retrieval：`reports/evaluation/v3_5_retrieval_benchmark_summary.md`。
- Answer：`reports/evaluation/v4_8_final_system_evaluation.md`。
- Reproducibility：`reports/evaluation/v4_7_selected_model_generation_stability.md`。
- Model selection：`reports/evaluation/v4_7_answer_model_selection.md`。
- 使用说明：`README.md`、`docs/evaluation.md`。
