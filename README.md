# Auto Manual RAG 项目说明

`auto_manual_rag` 是一个基于汽车用户手册 PDF 的 text-only RAG 项目。它的目标不是做一个最小问答 demo，而是用一个垂直领域场景练习 Python、FastAPI、本地模型调用、检索工程、chunk 结构化、评测体系和工程复盘。

请注意：当前 README 是阶段性内部说明，用于记录项目状态、技术路线、评测结果和下一步判断；它不是最终对外展示版 README，也不代表生产级系统。

本项目包含 [AGENTS.md](AGENTS.md)。使用 Codex、Claude Code 或其他 AI coding agent 修改项目之前，应先阅读并遵守其中的架构边界、反过拟合原则和评测驱动约束。

## 1. 项目定位

当前系统面向单本汽车用户手册 PDF，构建本地化 RAG 问答链路：

```text
汽车用户手册 PDF
  -> PDF page loading / cleaning
  -> ManualStructureParser
  -> ManualStructureSplitter
  -> Chroma dense vector index
  -> BM25 sparse index
  -> dense / bm25 / hybrid retrieval
  -> optional cross-encoder rerank
  -> context selection
  -> answer generation with citations
  -> retrieval evaluation
```

当前项目重点是：

- manual-aware parser；
- chunk metadata quality；
- dense + BM25 hybrid retrieval；
- optional cross-encoder rerank；
- evaluation-driven iteration；
- regression / failure case comparison。

项目不使用 LangChain / LlamaIndex。当前也不是多车型泛化系统，不具备图片、图标、按钮示意图或复杂版面理解能力。

## 2. 当前版本状态

当前可以视为 V3.5 Retrieval freeze 与 V4.5.1 Answer Evaluation reproducibility checkpoint。已经实现并验证的主要能力包括：

- PDF ingest、文本清洗和索引构建；
- `ManualStructureParser` 恢复 `chapter` / `section` / `subsection` 层级；
- `ManualStructureSplitter` 基于结构块生成 chunks；
- subsection heading 已进入 `ManualBlock.text`，用于增强检索语义；
- Chroma dense retrieval；
- BM25 sparse retrieval；
- dense + BM25 + RRF hybrid retrieval；
- TOC/noise filtering 和 content-level dedup；
- metadata-aware context selection；
- 可选 `BAAI/bge-reranker-base` cross-encoder rerank；
- 69-record text-only retrieval dev benchmark，其中 68 条 active、1 条 excluded；
- retrieval evaluation runner；
- retrieval benchmark consistency validation；
- rerank on/off comparison；
- V4 answer-eval provenance、sanitization、Exact Prompt Evidence snapshot 和 frozen evaluation semantics；
- 12-case V4.4 historical formal answer baseline 与 V4.5 human adjudication；
- 显式 generation configuration：`temperature=0.0`、`seed=42`、`stream=false`；
- 在固定 Ollama `0.33.2`、`qwen2.5:7b` model digest 和 generation configuration 下完成 4 cases x 3 runs 的 exact-output stability verification；
- FastAPI、Streamlit 和 CLI 基础链路。

当前默认链路仍是 hybrid no-rerank。rerank 指标收益明显，但延迟成本也明显，因此继续作为 optional high-precision mode，而不是默认行为。

V3.5 retrieval benchmark 已完成 chunk/index 对齐、recalibration、consistency validation、ambiguous-case adjudication、gold-equivalence adjudication 和 final freeze。V4.0-V4.5.1 已完成 answer-eval 基础设施、formal historical baseline、human failure taxonomy 和 generation reproducibility 验证。V4.6 已完成 failure analysis、fixed-generation reference 和 Condition Preservation 单变量实验；该 treatment 经因果隔离验证后判定为 `REJECT`，未进入稳定 Prompt，production RAG behavior 保持不变。下一阶段是 Resume-Ready Answer Model Selection。

V4.5 的 Human Full Pass 为 12-case dev diagnostic set 上的 `7/12`（58.33%），只用于当前 failure analysis，不代表 production accuracy、跨车型准确率或系统总体准确率。V4.4 保留为继承当时 generation defaults 的历史基线；后续严格 A/B 将使用 V4.5.1 固定参数建立独立 controlled reference，不覆盖历史 artifact。

## 3. 为什么汽车用户手册 RAG 不只是简单切块

汽车用户手册有几个现实难点：

- PDF 抽取会丢失字体、缩进、加粗、层级和图文布局信息；
- 目录、页码、页眉页脚、图标说明、表格残片容易污染索引；
- “警告 / 注意 / 说明 / 操作步骤”对答案安全性和可追溯性很重要；
- 用户问题经常需要精确定位手册证据，而不是泛泛解释；
- 相邻小节高度相似，例如安全带作用、系紧安全带、安全带检查、安全带清洁；
- naive page-level 或 fixed-size chunking 容易把多个主题混在一起，导致 metadata 错位和引用不稳定；
- 长列表问题可能需要多个 evidence 共同支撑，不能只看 top-1 chunk。

因此本项目没有停留在“PDF 切块 + embedding 检索”，而是逐步加入 manual-aware parser、hybrid retrieval、debug diagnostics 和 evaluation runner。

## 4. 系统整体流程

```text
data/raw/train_a.pdf
  -> PDFLoader
  -> clean_text
  -> ManualStructureParser
      -> ManualBlock(chapter, section, subsection, content_type, risk_level)
  -> ManualStructureSplitter
      -> Chunk(text, metadata, source_pages)
  -> Chroma dense index
  -> BM25 sparse index

query
  -> dense / bm25 / hybrid retrieval
  -> TOC/noise filter + dedup
  -> optional CrossEncoderReranker
  -> metadata-aware context selection
  -> prompt
  -> Ollama answer
  -> citations
```

评测链路独立于问答生成链路：

```text
data/eval/manual_eval_set.jsonl
  -> scripts/evaluate_retrieval.py
  -> metrics
  -> JSON / Markdown reports
  -> scripts/compare_rerank_evaluation.py
```

## 5. ManualStructureParser 设计

V3.5 parser 的核心策略是：

- `chapter`：由 `CHAPTER_TITLES` 精确匹配产生；
- `section`：只由 `EXACT_SECTION_TITLES` 精确匹配产生，是唯一合法 section 来源；
- `subsection`：由启发式规则加少量真实手册小标题白名单产生；
- `ManualBlock` 保留 `chapter`、`section`、`subsection`、`heading_path`；
- 新 `section` 出现时 reset `subsection`；
- `warning` / `caution` / `note` marker 不作为 subsection；
- subsection heading 已 prepend 到 `ManualBlock.text` 中，用于增强 retrieval 语义；
- `content_type` / `risk_level` 基于原始 block text 判断，避免被 prepend 的 subsection heading 干扰；
- parser 的目标是恢复 PDF 手册层级结构，不是为单个 query 写规则。

这个设计来自几轮 parser failure review。最终选择 exact section whitelist 的原因是：PDF 文本缺少视觉层级，弱启发式容易把正文短句、图标说明和目录残片误判成 section。section 作为评测和诊断的重要 metadata，宁可来源更保守，也不要让大量正文片段变成错误 section。

subsection 的职责不同。它用于补充 section 内部的小标题语义，例如相邻操作、提示块或短功能项。subsection 允许更轻量的启发式，但必须保守，且不能演变成针对单个 eval case 的规则集合。

当前不建议继续大改 parser。V3.5 frozen benchmark 显示 no-rerank top-5 命中 `66/68`，rerank 后为 `68/68`。剩余问题更适合进入 answer generation、answer evaluation、UI/API 或严格 latency measurement，而不是继续为个别 top-1 case 增加 parser 特例。

## 6. Chunking 与 Metadata

`ManualStructureParser` 输出 `ManualBlock`，`ManualStructureSplitter` 再将 block 转为最终 `Chunk`。

关键 metadata 包括：

- `chapter`
- `section`
- `subsection`
- `heading_path`
- `source_pages`
- `start_page` / `end_page`
- `content_type`
- `risk_level`
- `chunk_index`
- `split_strategy`

这些 metadata 的用途：

- 帮助 debug retrieval 结果；
- 支持 evidence / section / page 评测；
- 辅助 context selection；
- 支持 citation 展示；
- 帮助判断 chunk boundary、metadata missing、section misalignment 等问题。

需要注意：section metadata 依赖 parser 质量，不应单独作为成功标准。评测时应结合 page hit、quote hit、must_contain_terms 和 evidence_hit 综合判断。

当前索引计数必须区分存储层和可检索层：

- Chroma stored chunks：`1002`；
- BM25 / hygiene-filtered retrieval-eligible chunks：`981`；
- 被 BM25 hygiene filter 排除的 TOC/noise chunks：`21`。

因此不能把 `981` 表述为 Chroma 的原始存储数量。

## 7. Retrieval 设计

当前支持三种 retrieval mode：

| mode | 说明 |
| --- | --- |
| `dense` | 使用 Chroma + embedding 做语义召回。 |
| `bm25` | 使用 BM25 做关键词、术语和精确表达召回。 |
| `hybrid` | 使用 RRF 融合 dense 和 BM25 排名。当前主线模式。 |

Hybrid retrieval 的设计判断：

- dense retriever 负责语义相似问题；
- BM25 retriever 负责术语、短关键词、精确表达；
- RRF 做 rank-level fusion，不依赖两路分数尺度一致；
- chunk filtering 减少 TOC/noise/短噪声块进入候选；
- content-level dedup 减少完全重复内容占用 top-k；
- metadata-aware context selection 只做保守整理，不替代 retrieval；
- rerank 是可选精排阶段，不默认开启。

当前主线是 hybrid no-rerank。rerank 可在评测或高精度模式中启用，但不应在未做更广泛延迟和稳定性评估前默认开启。

## 8. Evaluation 设计

当前评测集：

```text
data/eval/manual_eval_set.jsonl
```

当前文件包含 69 条 text-only development records，其中 68 条 active cases 进入正式指标 denominator，1 条 `parking_detection_range_001` 保留但标记为 excluded。该 case 需要的表格数值未被当前 text-only chunk corpus 表示，属于 parser/table extraction coverage gap，不是 retrieval failure。

当前 benchmark 是与 V3.5 chunk strategy 绑定的 chunk-level retrieval benchmark：

- gold chunk ID 必须存在于当前 V3.5 index，并能独立提供问题所需 evidence；
- parser/chunk strategy 发生实质变化时必须 recalibrate benchmark，不能把 stale gold 静默计为 retrieval miss；
- multi-gold case 使用 ANY_OF 语义，命中任意一个 independently sufficient gold 即算 hit；
- MRR 使用排名最高的 gold chunk；
- excluded case 不进入 Hit@k / MRR denominator。

它是当前正式冻结的 V3.5 retrieval dev benchmark，但不是跨手册、跨车型的最终外部 test benchmark。

当前 eval cases 覆盖的 category 包括：

- `procedure`
- `warning_notice`
- `parameter_query`
- `maintenance_check`
- `explanation`
- `alarm_handling`
- `location_query`

核心指标包括：

- `evidence_hit@1` / `evidence_hit@3` / `evidence_hit@5`
- `MRR`
- `average_first_hit_rank`
- `page_hit@1`
- `term_coverage_ratio@1`
- `final_context_hit`
- noise rate
- duplicate rate
- improved / regressed / unchanged cases
- lost top-1 hit
- evidence hit@5 regression
- latency cost

指标解读：

- `evidence_hit@5` 主要看候选召回是否稳定；
- `evidence_hit@1` 和 `MRR` 主要看排序质量；
- `term_coverage` 只能辅助解释，不能单独代表证据命中；
- `section_hit` 依赖 metadata 质量，不能单独判断系统好坏；
- evaluation 是开发决策工具，不是对外宣传 benchmark。

更详细的评测说明见 [docs/evaluation.md](docs/evaluation.md)。

## 9. 当前 V3.5 评测结果

当前唯一正式 V3.5 baseline 来自 frozen reports：

- `reports/evaluation/v3_5_frozen_hybrid_no_rerank.json`；
- `reports/evaluation/v3_5_frozen_hybrid_rerank.json`；
- `reports/evaluation/v3_5_frozen_rerank_comparison.md`。

- total records = 69
- active case_count = 68
- excluded case_count = 1
- benchmark evidence = 99
- validation issues = 0
- dataset = `data/eval/manual_eval_set.jsonl`
- retrieval_mode = `hybrid`
- top_k = 5
- reranker = `BAAI/bge-reranker-base`
- rerank_top_n = 10
- rerank_output_top_k = 5

| Mode | evidence_hit@1 | evidence_hit@3 | evidence_hit@5 | MRR |
| --- | ---: | ---: | ---: | ---: |
| Hybrid no-rerank | 0.6618 | 0.9265 | 0.9706 | 0.7922 |
| Hybrid + rerank | 0.8676 | 0.9853 | 1.0000 | 0.9277 |

补充结果：

- Hit@1：`45/68 -> 59/68`；
- Hit@5：`66/68 -> 68/68`；
- `regressed_cases = 3`；
- `lost_top1_hit = 2`；
- `evidence_hit@5_regressions = 0`
- no-rerank elapsed = `21.11s`；
- rerank elapsed = `42.96s`。

elapsed 仅记录这一次运行。它不是严格 latency benchmark；正式比较需要同进程 warmup、重复运行、per-query latency 和 p50/p95。

当前结论：

1. V3.5 subsection hierarchy + subsection heading in block text 当前可以接受；
2. hybrid no-rerank 的 top-5 evidence hit 为 `66/68`，candidate retrieval 已具有较高 recall，但仍有两个 active case 未在 top-5 命中；
3. hybrid no-rerank 是当前默认且可复现的 frozen baseline；
4. rerank 能显著提升 top-1 evidence ranking；
5. rerank 将 top-5 提升到 `68/68`，但仍有少量 case-level regression，并带来推理成本，应继续 optional；
6. 当前剩余问题不应继续通过 parser 特例硬修；
7. 下一阶段转向 V4 Answer Quality / Answer Evaluation，而不是继续增加 retrieval complexity。

历史 V3.5 报告中的 `0.8841 / 0.9710` 等结果属于 pre-recalibration benchmark state，不能作为当前正式 baseline。pre-freeze recalibrated 到 frozen 的小幅变化来自 `wiper_caution_001` equivalent-gold adjudication，不代表 production retrieval improvement。

## 10. 当前已经确认的技术结论

- V3.5 parser/chunking 当前可以作为阶段 checkpoint。
- section 只由 exact whitelist 产生是合理选择，能降低正文误判。
- subsection heading 加入 block text 是有效改动，有助于 retrieval 语义。
- `content_type` / `risk_level` 不应被 subsection heading prepend 干扰。
- hybrid retrieval 是当前默认主线。
- no-rerank top-5 evidence recall 已达到 `66/68`，rerank 达到 `68/68`，不应为了少数 case 无限改 parser 或 retrieval。
- rerank 在当前 dev set 上有效，但不默认开启。
- 当前评测主要验证 retrieval，不等同于最终 answer generation 质量。
- 当前 69-record / 68-active benchmark 是 frozen V3.5 retrieval dev baseline，不是跨手册、跨车型的最终外部 benchmark。

## 11. 当前不应继续做的事

现阶段不建议继续投入以下方向：

- 为单个 case 添加 parser 特例；
- 继续扩大 subsection 启发式或白名单，只为提升个别样例；
- 把 69-case dev set 当作 final benchmark；
- 默认开启 rerank；
- 在未评测前同时改 parser、retrieval、rerank、prompt 多个模块；
- 用 prompt 掩盖 retrieval 或 metadata 问题；
- 根据单个 failure case 增加 BM25 penalty、metadata bonus 或 query-specific if-else；
- 将 generated index、reports、logs、PDF 或本地环境文件混入 commit。

这些限制不是为了停止迭代，而是为了避免项目进入“规则越补越多、系统越来越难解释”的状态。

## 12. 下一阶段建议工作方向

### 优先级 A：Resume-Ready Answer Model Selection

- 固定 retrieval、Prompt、Prompt Evidence、context configuration、evaluation semantics、`temperature=0.0` 和 `seed=42`；
- 只改变 Answer Model，比较当前 `qwen2.5:7b` 与少量高价值候选；
- 继续使用独立 `exp/*` 分支和 controlled reference，不把模型选择与 Prompt/retrieval 改动混合；
- 同时检查目标失败、pass-case regression、unsupported claim、safety 和 completeness；
- V4.6 rejected treatment 只保留实验报告，不作为当前系统能力。

### 优先级 B：固化 checkpoint 与项目展示

- 整理 V3.5 parser / retrieval / rerank summary；
- 清理未提交文件，区分代码、文档和运行产物；
- 保留关键 frozen reports 的结论；
- polish FastAPI / Streamlit 演示体验；
- 增加 query/result debug 页面或更清晰的 CLI 输出；
- 整理 docs，使项目更适合简历和面试讲解。

### 优先级 C：更高成本探索

- V4.7 Answer Model Benchmark；
- V4.8 Embedding / Retrieval Model Benchmark；
- V4.9 Query Transformation；
- 多手册 / 多车型泛化与最终外部评测；
- 表格、图片、图标、多模态能力；
- 更复杂的 query rewrite 或 agent workflow。

当前不建议马上进入优先级 C。除非先明确评测目标、延迟预算和验收标准，否则容易把系统继续做复杂，但收益不清晰。

## 13. 常用命令

### 13.1 构建索引

```bash
.venv/bin/python scripts/ingest_manual.py --rebuild
```

修改 parser、splitter、filtering、tokenizer、indexing 或 BM25 逻辑后需要 rebuild。单纯改 README 不需要 rebuild。

### 13.2 Inspect chunks

```bash
.venv/bin/python scripts/inspect_chunks.py \
  --page-range 156 159 \
  --show-full \
  --show-filtered \
  --limit 1000
```

按 query 检查 BM25 indexed chunks：

```bash
.venv/bin/python scripts/inspect_chunks.py \
  --query "安全带 锁舌 锁扣" \
  --show-full \
  --limit 20
```

### 13.3 Validate eval dataset

```bash
.venv/bin/python scripts/validate_eval_dataset.py data/eval/manual_eval_set.jsonl
```

正式 retrieval evaluation 前还必须验证 benchmark gold 与当前 index 一致：

```bash
.venv/bin/python scripts/validate_retrieval_eval_set.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --split dev
```

### 13.4 Hybrid no-rerank evaluation

```bash
.venv/bin/python scripts/evaluate_retrieval.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --retrieval-mode hybrid \
  --top-k 5 \
  --output /tmp/hybrid_no_rerank.json \
  --output-format json
```

### 13.5 Hybrid + rerank evaluation

```bash
.venv/bin/python scripts/evaluate_retrieval.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --retrieval-mode hybrid \
  --top-k 5 \
  --enable-rerank \
  --rerank-model-name BAAI/bge-reranker-base \
  --rerank-top-n 10 \
  --rerank-output-top-k 5 \
  --rerank-device auto \
  --output /tmp/hybrid_rerank.json \
  --output-format json
```

### 13.6 Compare rerank on/off

```bash
.venv/bin/python scripts/compare_rerank_evaluation.py \
  --baseline /tmp/hybrid_no_rerank.json \
  --experiment /tmp/hybrid_rerank.json \
  --output reports/evaluation/comparison.md \
  --output-format md
```

`reports/evaluation/` 下的运行产物默认不建议直接提交。需要保留阶段结论时，优先整理为 `docs/evaluation/` 下的总结文档。

### 13.7 Query CLI

```bash
.venv/bin/python scripts/query_manual.py \
  --question "如何正确使用安全带？" \
  --retrieval-mode hybrid
```

Debug retrieval：

```bash
.venv/bin/python scripts/query_manual.py \
  --question "充电时有哪些安全注意事项？" \
  --debug-retrieval \
  --retrieval-mode hybrid \
  --use-context-selection
```

### 13.8 启动后端和前端

```bash
uvicorn app.main:app --reload
```

```bash
streamlit run frontend/streamlit_app.py
```

### 13.9 测试

```bash
.venv/bin/python -m pytest tests -q
```

语法检查：

```bash
.venv/bin/python -m compileall app frontend scripts tests
```

## 14. 项目结构

```text
app/
  api/                 FastAPI routes
  core/                settings, logger, exceptions
  data/
    loaders/           PDF loading
    cleaners/          text cleaning
    parsers/           ManualStructureParser
    splitters/         ManualStructureSplitter
    schemas/           Document / ManualBlock / Chunk / Query models
  evaluation/          eval schemas, loader, metrics
  rag/
    embeddings/        local embedding client
    retrievers/        Chroma, BM25, hybrid, filters, context selector
    rerankers/         BaseReranker, NoopReranker, CrossEncoderReranker
    prompts/           answer prompt
    chains/            QAChain
  services/            ingest service

scripts/
  ingest_manual.py
  query_manual.py
  inspect_chunks.py
  validate_eval_dataset.py
  evaluate_retrieval.py
  compare_rerank_evaluation.py

tests/
  parser, reranker, comparison tests

data/eval/
  manual_eval_set.jsonl

docs/evaluation/
  evaluation and review notes

reports/evaluation/
  generated or retained evaluation reports
```

## 15. Known Limitations

- 当前是 text-only RAG，不处理图片、图标、按钮示意图、OCR 或复杂表格布局。
- 当前 retrieval benchmark 为 69 records / 68 active / 1 excluded 的 frozen V3.5 dev baseline，不是跨手册、跨车型的 final benchmark。
- 当前结果来自单一汽车用户手册，不能证明多车型或多品牌泛化。
- parser 使用 manual-specific exact section whitelist；这提升了当前手册结构质量，但迁移到新手册时需要复核。
- subsection whitelist 只能谨慎扩展，不能成为 query-specific 规则集合。
- 当前主要验证 retrieval，不代表最终 answer generation 已充分评估。
- 长列表、多 evidence 和 answer coverage 仍需要更系统的 answer-level evaluation。
- rerank 有明确推理成本，当前不默认开启；单次 elapsed 不足以形成严格 latency 结论。
- section metadata 仍可能缺失或错位，评测时不能只看 section_hit。
- FastAPI / Streamlit 仍是基础演示形态，不是完整产品界面。

## 16. 面向简历的可提炼亮点

后续整理最终对外版 README 或简历时，可以从以下方向提炼：

- 构建了基于汽车用户手册 PDF 的本地化 RAG 系统；
- 设计 manual-aware parser，恢复 `chapter` / `section` / `subsection` 层级；
- 实现 Chroma dense retrieval、BM25 sparse retrieval 和 RRF hybrid retrieval；
- 构建 TOC/noise filtering、content-level dedup 和 chunk inspection 诊断工具；
- 接入可关闭的本地 cross-encoder rerank；
- 构建 69-record、68-active 的 frozen text-only retrieval dev benchmark、consistency validator 和 evaluation runner；
- 在 frozen V3.5 benchmark 上建立 hybrid no-rerank `evidence_hit@1=0.6618`、rerank `evidence_hit@1=0.8676` 的可复现基线；
- 建立 rerank on/off comparison、failure review 和 regression analysis 工作流。

这些亮点应基于当前 dev set 和工程实现来描述，不要扩展成 production-ready、多车型泛化或多模态能力。

## 17. Git 提交注意事项

提交前建议运行：

```bash
git diff --check
git status
```

如果修改了 Python 代码，至少运行：

```bash
.venv/bin/python -m compileall app frontend scripts tests
.venv/bin/python -m pytest tests -q
```

不要提交：

- `.env`
- `.venv/`
- `data/raw/`
- `data/chroma/`
- `data/processed/*.pkl`
- `logs/`
- 模型缓存
- `/tmp` 下的运行产物
- 未经整理的 `reports/evaluation/` 临时报告
- 原始 PDF 手册
