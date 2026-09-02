# V3.5 Retrieval Benchmark Reference Audit

本审计在 repository-wide documentation synchronization 修改前生成，用于区分当前性引用、历史记录、歧义引用、过期引用和生成产物。

## 1. 搜索范围与口径

搜索范围包括：

- `README.md`、`AGENTS.md`；
- `docs/`；
- `reports/evaluation/`；
- `scripts/`、`app/evaluation/`、`tests/`；
- `data/eval/` 中的文本说明和 JSONL。

排除了 `.git/`、`.venv/`、Chroma/BM25 二进制索引、模型缓存和日志。

初筛共命中：

- 56 个文件；
- 9,392 个匹配行；
- 其中 28 个 report files，四份逐 case JSON 报告贡献了绝大多数匹配行。

按文件类型统计：

| 类型 | 文件数 |
| --- | ---: |
| root status documents | 2 |
| docs | 11 |
| reports | 28 |
| code / scripts / tests | 14 |
| eval dataset | 1 |

匹配行数量不等于独立 benchmark 结论数量；JSON 中每条 case 的重复字段只按 generated artifact 处理。

## 2. 分类结果

### CURRENT_REFERENCE / STALE_REFERENCE

以下文件用于描述当前状态，需要同步到 frozen baseline：

| 文件 | 审计结论 |
| --- | --- |
| `README.md` | 将旧的 V3.5 pre-recalibration 指标 `0.8841 / 0.9710` 作为当前结果，属于 stale reference。 |
| `docs/v3.5_readme.md` | 与 README 相同，属于 stale duplicate。 |
| `AGENTS.md` | 当前阶段和评测结论停留在 V3.2，属于 stale project-status reference。 |
| `docs/evaluation.md` | 已有 freeze 说明，但缺少完整 methodology、正式指标、validation 和 latency 解读。 |
| `docs/rerank_design.md` | 历史设计正文可保留，但“当前结论以 V3.2 为准”的状态提示已过期。 |
| `docs/evaluation/eval_set_design.md` | 设计历史有效，但需要声明当前 69 records / 68 active 的 frozen 状态。 |

### HISTORICAL_REFERENCE

以下文档明确记录特定历史阶段，保留旧指标，不改写为当前 baseline：

- `docs/evaluation/rerank_evaluation_summary.md`：V3.2 rerank 实验；
- `docs/evaluation/failure_case_review.md`：V3.2 failure review；
- `docs/evaluation/chunk_metadata_review.md`：V3.4-step1 诊断；
- `docs/evaluation/v3_4_parser_fix_summary.md`：V3.4 parser 实验；
- `docs/evaluation/parser_refactor_plan.md`：parser refactor 历史计划；
- `docs/rerank_design.md` 正文中的 V3.0-V3.2 设计背景；
- `docs/evaluation/eval_set_design.md` 中的 29 → 69 扩展历史。

### AMBIGUOUS_REFERENCE

- README 中“69-case dev set 不是 final benchmark”与“当前 V3.5 baseline”并存但未区分。同步后应明确：它是 frozen V3.5 retrieval dev benchmark，但不是跨手册、跨车型的最终外部 test benchmark。
- README 中单次 elapsed 和倍数被直接用于 latency 结论。同步后仅保留为单次 run 记录。

### GENERATED_ARTIFACT

以下历史 artifacts 不覆盖、不重写：

- legacy V3.5 reports；
- V3.5 recalibration audit；
- pre-freeze recalibrated reports；
- failure review；
- gold-equivalence adjudication；
- V3.1/V3.2/V3.4 历史 reports。

当前 frozen artifacts 为：

- `v3_5_frozen_hybrid_no_rerank.json`；
- `v3_5_frozen_hybrid_rerank.json`；
- `v3_5_frozen_rerank_comparison.md`。

### CODE / TEST / SCRIPT REFERENCES

`app/evaluation/`、evaluation scripts 和 tests 中未发现把旧指标硬编码为当前正式 baseline 的注释、docstring 或断言。本轮不修改 evaluator logic。

## 3. 数据与索引核实

- `manual_eval_set.jsonl`：69 records，ID 集合与 HEAD 一致；
- active cases：68；
- excluded cases：1；
- benchmark evidence：99；
- consistency validation issues：0；
- Chroma stored chunks：1,002；
- BM25 / hygiene-filtered retrieval-eligible chunks：981；
- BM25 filtered chunks：21。

数据集相对 HEAD 的语义变化均落在 V3.5 recalibration、metadata/boundary repair、multi-gold adjudication、exclusion 和 notes 范围内。未发现无法解释的 case ID 增删或其他字段变化。

## 4. 同步决策

1. 当前性文档使用 frozen metrics。
2. 历史文档和历史 reports 保留原指标，并明确版本上下文。
3. legacy → recalibrated 的变化解释为 benchmark truth 校准，不解释为 production regression。
4. pre-freeze → frozen 的变化来自 `wiper_caution_001` equivalent-gold adjudication，不解释为 production improvement。
5. 不修改 retrieval、rerank、parser、dataset 或 evaluator logic。
