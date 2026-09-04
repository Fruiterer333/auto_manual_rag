# Auto Manual RAG 源码学习地图

这不是目录说明，而是面试前的代码所有权学习顺序。目标是能解释输入、输出、算法、边界和失败模式，而不是背文件名。

## 推荐阅读路径

```text
config / schemas
-> ingest_service
-> parser / splitter
-> Chroma + BM25 + HybridRetriever
-> filters / context_selector
-> QAChain / answer_prompt / Ollama
-> retrieval metrics / benchmark validation / answer evaluator
-> FastAPI / CLI / Streamlit
```

## P0：必须深入解释

### `app/services/ingest_service.py`

- **Why it matters**：串起 PDF 到 Chroma/BM25 的完整数据管道，是应用离线准备阶段的入口。
- **Core**：`ingest_manual()`、`IngestResult`、`_distribution()`、`_length_stats()`。
- **Input**：PDF 路径、rebuild、chunk size/overlap、Settings。
- **Output**：页数、chunk 数、成功状态；副作用是写入 Chroma 和 BM25 index。
- **Key algorithm**：load -> clean -> parse -> structure split -> fallback split -> batch embed -> Chroma write -> BM25 build。
- **Key boundary**：Dense 和 sparse 必须消费同一批 chunks；rebuild 会 reset Chroma；BM25 build failure 不应静默忽略。
- **Interview questions**：为什么 parser 输出为空时保留 fallback？为什么 BM25 在 Chroma 之后构建？哪些修改要求重新 ingest？

### `app/data/parsers/manual_structure_parser.py`

- **Why it matters**：决定手册层级、block boundary、安全 marker 和 chunk 语义来源，是最有领域价值的模块。
- **Core**：`ManualStructureParser.parse()`、`ParserState`、`_classify_line()`、`_is_subsection_heading()`、`_flush_state()`、`_flush_buffer()`。
- **Input**：按页的 `Document` 列表。
- **Output**：带 chapter/section/subsection/heading_path/content_type/risk_level 的 `ManualBlock`。
- **Key algorithm**：逐行分类；状态保存当前层级和 buffer；遇到新标题或安全 marker 时按规则 flush；subsection prepend 到 block text，但 content classification 使用原始 body。
- **Key boundary**：section 使用保守 exact titles；subsection 可轻量启发式；目录页不更新 hierarchy；不能把问题词或评测页码写进规则。
- **Interview questions**：为什么需要 parser state？新 section 为什么 reset subsection？为什么 section 不进正文、subsection 进正文？跨页 warning 如何保持？

### `app/data/splitters/manual_structure_splitter.py`

- **Why it matters**：把语义 block 转成最终可索引 chunks，并决定长列表/警告是否被切断。
- **Core**：`split_blocks()`、`_split_block_text()`、`_split_long_text()`、`_find_boundary()`、`_find_list_item_boundary()`。
- **Input**：`ManualBlock` 列表和 chunk size/overlap。
- **Output**：确定性 UUID、hierarchy 和 source-page metadata 完整的 `Chunk` 列表。
- **Key algorithm**：短 block 保持完整；warning/caution/note/procedure 允许一定超长；长文本优先在列表项、marker、句号或换行处分割。
- **Interview questions**：为什么安全块允许超过 chunk size？overlap 的作用和代价是什么？chunk ID 如何保持可校验？

### `app/rag/retrievers/bm25_retriever.py`

- **Why it matters**：提供 lexical retrieval，支撑系统名、按钮、故障码和精确短语检索。
- **Core**：`build_index()`、`load_index()`、`search()`、`_coverage_info()`、`_apply_coverage_penalty()`。
- **Input**：build 接收 chunks；search 接收 query 与 top_k。
- **Output**：持久化 BM25 index；检索返回带 BM25 score、rank、coverage 和 penalty metadata 的 `RetrievedChunk`。
- **Key algorithm**：build 前 hygiene filter；使用 BM25Okapi；query token 过滤后计算分数；动态 coverage term 只做 soft penalty；归一化后排序。
- **Key boundary**：不保存 embedding；coverage terms 从 query 动态生成，不维护面向 smoke tests 的领域白名单；penalty 不做硬过滤。
- **Interview questions**：中文不使用 jieba 怎么 tokenize？为什么 score penalty 要保守？为什么 BM25 index 要保存 chunk metadata？

### `app/rag/retrievers/tokenizer.py`

- **Why it matters**：BM25 质量高度依赖中文和英文数字 token 表示。
- **Core**：`tokenize_for_bm25()`、`tokenize_query_for_bm25()`、`filter_query_tokens()`、`extract_coverage_terms()`。
- **Input**：document text 或 query。
- **Output**：英文数字 token、中文单字和 2-5 gram；query 还返回保守过滤结果。
- **Key algorithm**：regex 保留 EPB/12V 等 alphanumeric；中文字符 n-gram 自然覆盖复合词；弱词只在剩余核心信号足够时移除。
- **Interview questions**：为什么 n-gram 适合这类手册？过多 n-gram 有什么索引成本？为什么不能把“充电/胎压”做成固定 core terms？

### `app/rag/retrievers/hybrid_retriever.py`

- **Why it matters**：实现 dense/bm25/hybrid 三模式、RRF 融合和统一 debug metadata。
- **Core**：`search()`、`_rrf_fuse()`、`_merge_result()`、`_annotate_rank()`。
- **Input**：question、query embedding、top_k/candidate_k、retrieval mode。
- **Output**：按最终模式排序、过滤、去重的 `RetrievedChunk`。
- **Key algorithm**：两路独立召回并标 rank；hybrid 对同 chunk ID 累加 reciprocal rank；合并 dense distance、dense/BM25 rank/score；fusion 后再 filter/dedup。
- **Interview questions**：为什么不归一化两路原始分数？同一 chunk 两路命中时 metadata 如何合并？RRF 能否解决互补 Evidence 问题？

### `app/rag/retrievers/context_selector.py`

- **Why it matters**：决定最终送入模型的有限 Evidence，而不是只展示 retrieval top-k。
- **Core**：`select_contexts()`、`assemble_final_answer_contexts()`、`enforce_max_context_chars()`、`expand_neighbor_contexts()`。
- **Input**：question、候选 RetrievedChunks、top_k、开关和预算。
- **Output**：保留 selection score 和原顺序语义的最终 contexts。
- **Key algorithm**：关键词/意图驱动的轻量 metadata bonus；最终先限制数量，再累计字符；neighbor expansion 默认关闭。
- **Key boundary**：selection 不能掩盖 retrieval 失败；bonus 必须可解释；最终 budget 不重新排序。
- **Interview questions**：candidate_k、top_k、final contexts 有什么区别？为什么 neighbor expansion 默认关闭？字符预算如何处理超长第一条 Evidence？

### `app/rag/chains/qa_chain.py`

- **Why it matters**：production query 的主编排器，定义 retrieval 到 citations 的真实顺序和可审计不变量。
- **Core**：`QAChain.answer()`、`answer_with_trace()`、`_resolve_retrieval_mode()`、`_post_process_answer()`。
- **Input**：question、top_k、可选 retrieval mode。
- **Output**：`QueryResponse`；trace 路径额外返回 raw answer 和 Exact Prompt Evidence。
- **Key algorithm**：embed -> retrieve -> filter/dedup -> optional rerank -> context selection -> optional expansion -> final filter/dedup/budget -> prompt -> Ollama -> sanitizer -> citations。
- **Key boundary**：Prompt 与 citations 必须来自同一组 final contexts；无 Evidence 时固定保守回答；不让 Prompt builder 的 defensive budget 产生不可见 citation 差异。
- **Interview questions**：如何证明 citation 与模型 Evidence 一致？rerank 插在哪一层？为什么 answer_with_trace 不直接改变 API schema？

### `app/rag/prompts/answer_prompt.py`

- **Why it matters**：定义 Evidence 表示、回答约束和模型实际可见快照。
- **Core**：`assemble_answer_prompt()`、`PromptEvidenceSnapshot`、`_format_evidence()`、`_select_prompt_evidence()`。
- **Input**：question、最终 chunks、max contexts/chars。
- **Output**：Prompt 字符串和按 E1-E5 排序的 Evidence snapshots。
- **Key algorithm**：格式化 page/hierarchy/content type；限制数量和字符；单个首条过长时尾部截断并标记；其余超预算 Evidence 整条不加入。
- **Key boundary**：Prompt 只处理 generation contract，不修 retrieval；内部 E ID 不进入用户答案；证据不足时拒绝猜测。
- **Interview questions**：为什么需要 Evidence ID 和边界？条件差异与真正冲突如何区分？为什么 Prompt 仍保留 defensive budget？

### `app/evaluation/metrics.py`

- **Why it matters**：定义 retrieval 的 Hit@K、MRR、term/noise/duplicate 等正式计算方式。
- **Core**：`evaluate_case_retrieval()`、`aggregate_results()`、`_is_evidence_hit()`、`_first_evidence_hit_rank()`。
- **Input**：`EvalCase`、retrieved/final contexts、mode 和 top_k。
- **Output**：逐 case `RetrievalEvalResult` 和聚合 metrics。
- **Key algorithm**：存在 gold chunk IDs 时以 chunk ID 为准；multi-gold 命中任一即可；first gold rank 计算 MRR；excluded case 在 loader/runner 层不进入结果。
- **Key boundary**：page/section/term 是辅助指标；cross-page repeated content 不自动等于错误；ANY_OF 不能代表互补 Evidence 齐全。
- **Interview questions**：Hit@K 与 MRR如何互补？为什么 gold ID 存在时不再用宽松语义 fallback？为什么 any_term_hit 容易虚高？

### `app/evaluation/benchmark_validation.py`

- **Why it matters**：阻止 parser/chunk 变化后 stale gold 被静默计为 retrieval miss。
- **Core**：`validate_retrieval_benchmark()`、`ensure_retrieval_benchmark_valid()`、`_validate_evidence()`。
- **Input**：eval cases 和当前 BM25 chunk store。
- **Output**：active/excluded/evidence counts、issue types；不一致时 fail-fast。
- **Key algorithm**：逐 gold 检查 chunk ID、quote、page、chapter、section、subsection、heading path；excluded case 跳过 gold requirement。
- **Interview questions**：为什么 benchmark 也需要版本管理？为什么不能按 retriever top-1 反向选 gold？如何处理 parser 升级？

### `app/evaluation/answer_evaluator.py`

- **Why it matters**：区分 deterministic diagnostics、模型实际 Evidence 与人工 answer-quality rubric。
- **Core**：`AnswerEvalCase`、`AnswerCaseResult`、`evaluate_answer_response()`、`build_answer_evaluation_run()`、`HUMAN_REVIEW_RUBRIC`。
- **Input**：answer eval case、QueryResponse、raw answer、Prompt Evidence 和 elapsed。
- **Output**：Exact Prompt Evidence、citations、term/structure/insufficient/leak checks 及待人工评分字段。
- **Key algorithm**：术语覆盖和禁词只作 deterministic proxy；人工 rubric 分为 groundedness/correctness/completeness/condition/safety，并标 unsupported/critical omission。
- **Key boundary**：lexical proxy 不能覆盖人工判断；citation quote 不能替代 Prompt Evidence；12-case proposed review 不能叫 production accuracy。
- **Interview questions**：为什么 raw 与 final answer 都要记录？五维 rubric 如何区分？hard negative 如何评估？

## P1：必须理解职责和调用关系

| 文件 | 必须掌握 |
| --- | --- |
| `app/core/config.py` | Settings 是模型、检索、rerank、预算和路径的唯一默认配置来源；`.env` 可覆盖。 |
| `app/data/schemas/models.py` | Document、ManualBlock、Chunk、RetrievedChunk、Citation、QueryRequest/Response 的边界。 |
| `app/data/loaders/pdf_loader.py` | PyMuPDF 如何按页生成 Document，以及 page/source metadata。 |
| `app/data/cleaners/text_cleaner.py` | 清洗哪些空白和控制字符；哪些结构不能在清洗阶段丢失。 |
| `app/rag/embeddings/local_embedding.py` | sentence-transformers 的 document/query encoding 和 normalized embeddings。 |
| `app/rag/retrievers/chroma_retriever.py` | collection 创建、cosine metadata、chunk 写入、distance/score 恢复。 |
| `app/rag/retrievers/chunk_filters.py` | TOC/noise detection、stage summary、exact normalized content dedup 和保留策略。 |
| `app/rag/rerankers/*` | Noop 与 CrossEncoder 共享接口；默认开关关闭，实验可替换。 |
| `app/rag/llms/ollama_client.py` | `/api/generate` payload、temperature/seed/think、timeout、runtime version/digest metadata。 |
| `app/evaluation/loader.py` | JSONL 解析、category/intent/split/limit 过滤和 excluded cases。 |
| `app/evaluation/answer_provenance_validation.py` | answer case evidence 与 retrieval benchmark/current corpus 的一致性。 |
| `app/evaluation/human_adjudication.py` | 人工评分 consolidation、Full Pass 和 severe failure 规则。 |
| `app/api/deps.py` | QAChain 的依赖构造和 API 生命周期。 |
| `app/api/routes/query.py` | 请求参数如何传入 QAChain，以及非法 mode 的异常边界。 |
| `app/api/routes/ingest.py` | API ingest 到 service 的参数映射。 |
| `app/main.py` | FastAPI app、router 注册与日志初始化。 |

## P2：知道用途即可

| 文件或目录 | 用途 |
| --- | --- |
| `scripts/ingest_manual.py` | ingest CLI。 |
| `scripts/query_manual.py` | 普通问答和 debug retrieval CLI。 |
| `scripts/inspect_chunks.py` | 从 BM25 index 查看 chunks 与 filter 标记。 |
| `scripts/evaluate_retrieval.py` | retrieval benchmark runner 与报告输出。 |
| `scripts/evaluate_answers.py` | answer generation/evaluation artifact runner。 |
| `scripts/validate_*` | dataset、benchmark、answer provenance 的 fail-fast 入口。 |
| `scripts/compare_rerank_evaluation.py` | rerank/no-rerank case-level comparison。 |
| `scripts/verify_generation_reproducibility.py` | representative cases 重复运行稳定性。 |
| `frontend/streamlit_app.py` | 调 FastAPI `/query`，展示 retrieval mode、回答和可展开 citations。 |
| `app/core/logger.py` | 统一日志格式和文件 handler。 |
| `app/rag/utils/citation_utils.py` | 从最终 chunk 生成 relevant quote。 |
| `app/rag/utils/internal_evidence_refs.py` | 只清理明确 Evidence 引用，不误删裸 E1 故障码。 |

## 面试前动手检查

1. 手画一遍 ingest 和 query 两条时序图。
2. 用一个 query 跟踪 `candidate_k -> fused -> selected -> final contexts -> Prompt Evidence -> citations`。
3. 手算两个 Dense/BM25 排名的 RRF score。
4. 从 eval JSONL 找一个 multi-gold case，解释 ANY_OF 和 MRR。
5. 从 V4.7 artifact 对比同一 case 的三个模型 Prompt Evidence 和答案。
6. 运行 parser、answer prompt、benchmark validation 的单元测试并解释断言。
7. 能指出至少三个系统限制，并说明为什么当前没有继续堆功能。
