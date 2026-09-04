# Auto Manual RAG 简历项目材料

本文档提供可直接整理进中文技术简历的项目事实。它不是完整个人简历，也不应脱离 [冻结技术事实](technical_facts.md) 扩大指标含义。

## 推荐项目名称

**Auto Manual RAG：汽车用户手册可追溯智能问答应用**

## 一句话定位

面向汽车用户手册构建本地 RAG 应用，通过层级感知解析、Dense + BM25 + RRF 混合检索、Grounded Generation 和可追溯评测，将非结构化 PDF 转化为带页码、章节和证据引用的问答服务。

## 推荐技术栈

- Backend：Python、FastAPI、Pydantic、Requests
- Data pipeline：PyMuPDF、自定义 manual-aware parser/splitter
- Retrieval：Chroma、BGE Embedding、BM25、RRF、可选 Cross-Encoder Rerank
- Generation：Ollama、`qwen3.5:9b`
- Evaluation：JSONL benchmark、自定义 retrieval/answer evaluator、pytest
- UI：Streamlit

不要加入项目未使用的 LangChain、LlamaIndex、Docker、Redis、Kafka、Agent、MCP 或 GraphRAG。

## 三条 Resume Bullets

1. 设计汽车用户手册 ingestion pipeline，基于 PyMuPDF 和自定义层级解析器恢复 `chapter/section/subsection/heading_path`，保留 warning、caution、procedure 与跨页 metadata，为精确检索和引用溯源提供结构化数据基础。
2. 实现 Chroma Dense + BM25 Sparse + RRF Hybrid Retrieval，并加入 TOC/noise filtering、内容去重和 metadata-aware context selection；在 68 条 active retrieval dev queries 上，稳定 no-rerank 配置达到 Hit@5 `0.9706`、MRR `0.7922`。
3. 构建 Grounded Generation 与 retrieval/answer 双层评测体系，记录 Exact Prompt Evidence、raw/final answer 和 citations；通过固定 Evidence 的三模型受控比较选择本地 `qwen3.5:9b`，同时保留失败实验与回归边界。

## 四条 Resume Bullets

1. 设计并实现汽车用户手册结构化 ingestion pipeline，从 PDF 中恢复章节、小节和 heading path，保留内容类型、风险等级和跨页信息，降低固定长度切块造成的主题与引用错位。
2. 构建 Dense、BM25 和 RRF 双路召回，集中处理目录噪声、重复 chunk 与 query coverage，并使用 metadata-aware selection 将最终 Evidence 限制在 5 条、6000 字符内。
3. 建立可追溯的 Grounded Generation 链路，通过 FastAPI、CLI 和 Streamlit 提供问答入口，返回页码、章节和摘录；记录模型实际可见 Evidence、raw answer、sanitized answer 与 citations 供审计。
4. 建立 69-record retrieval benchmark 和 12-case answer diagnostic set，完成 benchmark recalibration、multi-gold/排除样例治理、可复现生成和受控模型选型；在 Evidence 12/12 invariant 下选择 `qwen3.5:9b` 作为本地默认模型。

## 简短版项目描述

构建汽车用户手册本地 RAG 应用，完成结构感知 PDF 解析、Dense + BM25 + RRF 混合检索、证据过滤与上下文控制、基于 Evidence 的本地模型回答以及页码/章节引用。配套实现 retrieval 与 answer evaluation、Exact Prompt Evidence trace、benchmark consistency validation 和受控模型选型。

## 完整版项目描述

项目解决汽车用户手册 PDF 中章节层级丢失、相近小节术语重叠、目录和图例污染检索以及安全条件容易在生成中被弱化的问题。数据侧使用自定义 manual-aware parser/splitter 恢复 chapter、section、subsection 和 heading path；检索侧使用 Chroma Dense 与 BM25 双路召回，通过 RRF 融合，并增加 TOC/noise filtering、exact content dedup 和 metadata-aware context selection。回答侧将最终 Evidence 限制为最多 5 条、6000 字符，由 Ollama `qwen3.5:9b` 基于证据生成中文回答并返回结构化 citations。

工程上建立了与当前 chunk strategy 对齐的 retrieval benchmark、answer diagnostic set、Exact Prompt Evidence 与 raw/final answer trace。项目不是围绕个别问题反复调参，而是使用 benchmark recalibration、失败归因、单变量实验和明确的 ACCEPT/REJECT 标准做决策；无效的 Prompt treatment 被拒绝，最终模型则在 Prompt Evidence 完全不变的三模型比较中确定。

## 可安全使用的量化指标

- “在当前单手册、68 条 active retrieval dev queries 上，hybrid no-rerank 达到 Hit@1 `0.6618`、Hit@3 `0.9265`、Hit@5 `0.9706`、MRR `0.7922`。”
- “V3.5 retrieval benchmark 包含 69 records、68 active cases、1 excluded case 和 99 条 gold evidence，consistency validation issues 为 0。”
- “三模型比较中，同一 case 的 Prompt Evidence 对 12/12 cases identity/order/text 完全一致。”
- “选定模型在当前固定 Ollama/model digest/config 下完成 4 cases x 3 runs 的 exact-output stability verification。”
- “12-case answer dev diagnostic set 的 PROPOSED Human Full Pass 为 10/12。”使用时必须保留 PROPOSED、dev diagnostic 和 single-manual 限定，不建议在简历主 bullet 中换算为百分比。

## 禁止使用的夸大表述

- 系统准确率达到 97%。
- 回答准确率达到 83.3%。
- 生产级零幻觉问答。
- 支持任意车型、任意手册或多模态内容。
- reranker 将线上延迟提高一倍。
- 固定 temperature/seed 后可跨机器完全复现。
- 项目使用 Agent、MCP、GraphRAG、LangChain 或 LlamaIndex。

## 面试时的 Claim 说明

1. Hit@K 和 MRR 衡量当前 frozen retrieval dev benchmark 上的 gold-evidence 排名，不是 answer accuracy。
2. Answer `10/12` 来自 12-case dev diagnostic set 的 PROPOSED rubric review，不是正式外部 test 或 production accuracy。
3. 模型 elapsed 是单次本地离线实验观察，不是线上 SLA、p50 或 p95。
4. 所有手册数据由用户自行合法提供；仓库不分发第三方原始 PDF、索引或模型权重。
