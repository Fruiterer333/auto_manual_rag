# Evaluation Methodology

本项目分别评估 retrieval ranking 和 answer quality。两类评测共享可追溯的手册 Evidence，但指标含义不同，不能将 Hit@K 解释为回答准确率。

## Scope

- 当前语料来自单份汽车用户手册。
- Retrieval dataset 包含 69 条 records，其中 68 条 active、1 条 excluded。
- Answer dataset 是 12-case dev diagnostic set，用于分析回答使用 Evidence 的方式，不是 production benchmark。
- 评测面向 text-first pipeline，不覆盖必须依赖图标、图片或复杂表格布局的问题。

## Retrieval Dataset

`data/eval/manual_eval_set.jsonl` 每条 case 记录：

- question、category、intent type；
- expected page/section/content type；
- must-contain terms；
- 可追溯到当前 indexed chunk 的 evidence；
- 一个或多个 independently sufficient gold chunk IDs；
- active/excluded 状态及原因。

Gold Evidence 来自原始手册事实与当前 chunk representation，不能根据 retriever 的 top-k 结果反向定义。

### Multi-gold semantics

一个问题存在多个独立且等价的正确 chunks 时，命中任意一个 gold chunk 即视为 evidence hit；MRR 使用排名最高的正确 gold。需要多个互补 chunks 才能完整回答的问题不能用这一 ANY_OF 语义证明 evidence 已完整覆盖。

### Excluded cases

当 text-only corpus 无法表示问题需要的事实时，case 保留 exclusion reason，但不进入 Hit@K 或 MRR 分母。Excluded case 不是 retrieval miss。

## Benchmark Consistency Validation

正式 retrieval evaluation 前运行：

```bash
.venv/bin/python scripts/validate_retrieval_eval_set.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --split dev
```

Validator 检查 gold chunk ID、quote、page、section、subsection 和 heading path 是否仍与当前 index 一致。Parser 或 chunk strategy 发生实质变化时，必须先重新审计 benchmark；stale gold 不得静默计为 retrieval miss。

## Retrieval Metrics

| Metric | Meaning |
| --- | --- |
| Hit@K | top-k 是否包含任一 gold Evidence。 |
| MRR | 首个 gold Evidence 排名的倒数均值。 |
| Page/section hit | 基于 metadata 的辅助命中指标。 |
| Term coverage | top-k 文本对 must-contain terms 的覆盖程度。 |
| Noise rate | top-k 中 TOC/noise chunks 的比例。 |
| Duplicate rate | chunk ID、同页文本或跨页重复内容比例。 |
| Final context hit | context selection 后的 Evidence 是否仍包含 gold。 |

`section_hit` 和 `content_type_hit` 依赖 parser metadata 质量，只能辅助解释。`any_term_hit` 容易因宽泛词而虚高，也不能单独作为 evidence hit。

运行稳定 hybrid 配置：

```bash
.venv/bin/python scripts/evaluate_retrieval.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --retrieval-mode hybrid \
  --top-k 5 \
  --output /tmp/hybrid.json \
  --output-format json
```

启用可选 reranker：

```bash
.venv/bin/python scripts/evaluate_retrieval.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --retrieval-mode hybrid \
  --top-k 5 \
  --enable-rerank \
  --output /tmp/hybrid-rerank.json \
  --output-format json
```

## Answer Evaluation

`data/eval/answer_eval_set.jsonl` 定义问题范围、required points、forbidden claims、insufficient-evidence behavior 和 Evidence provenance。

Answer artifact 同时保存：

- Exact Prompt Evidence：模型实际看到的 Evidence identity、顺序和文本；
- raw answer 与 post-processed final answer；
- citations；
- model、digest、Ollama version 和 generation configuration；
- deterministic diagnostic checks。

人工评分维度包括 groundedness、correctness、completeness、condition handling 和 safety preservation，并单独标记 unsupported claim 与 critical safety omission。Lexical coverage 和固定短语检查只作为 diagnostic proxy，不能覆盖人工判断。

运行：

```bash
.venv/bin/python scripts/validate_answer_eval_set.py

.venv/bin/python scripts/evaluate_answers.py \
  --dataset data/eval/answer_eval_set.jsonl \
  --retrieval-mode hybrid \
  --model qwen3.5:9b \
  --think false \
  --top-k 5 \
  --output /tmp/answer-eval.md \
  --json-output /tmp/answer-eval.json
```

Answer evaluation 会调用本地模型；retrieval evaluation 不需要生成答案。

## Interpretation Boundaries

- Hit@K 和 MRR 衡量当前 retrieval dev benchmark 上的 Evidence 排名，不是 end-to-end accuracy。
- 当前数据集来自单本手册，不能推断跨品牌、跨车型泛化能力。
- 本地 elapsed 是离线运行记录，不是 production SLA、p50 或 p95。
- 固定 temperature/seed 的重复运行稳定性只适用于已记录的模型 digest、Ollama 版本、后端和硬件环境。
- 单个 case 的失败不能直接成为 query-specific retrieval 或 Prompt 规则。

最终机器可读结果与必要报告见 [Evaluation Evidence](../reports/evaluation/README.md)。
