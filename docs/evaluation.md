# V3.0.2 Evaluation

V3.0.2 的目标是建立可复现、可量化、可比较的评测体系，不是继续调检索规则、prompt 或 tokenizer。当前四个 smoke tests 只能用于发现明显回归，不能作为唯一优化目标。

## Dataset

默认评测集：

```bash
data/eval/manual_eval_set.jsonl
```

JSONL 每行一条 `EvalCase`。关键字段：

- `id`：唯一样例 ID。
- `question`：用户问题。
- `category`：问题类别，例如 `procedure`、`warning_notice`、`alarm_handling`。
- `intent_type`：更细的意图类型，例如 `specific_operation`、`safety_notice`。
- `expected_pages`：期望命中的页码，可为空。
- `expected_sections`：优先命中的 section，可为空。
- `acceptable_sections`：可接受的相关 section。
- `expected_content_types`：期望命中的 `warning`、`caution`、`procedure` 等类型。
- `must_contain_terms`：检索内容或答案中应覆盖的关键词。
- `answer_must_cover`：后续 answer evaluation 可用的答案要点。
- `forbidden_content`：答案不应包含的内容。
- `evidence`：来自真实手册 chunk 的证据，包含 `page`、`section`、`chunk_id`、`quote`。
- `split`：默认 `dev`，预留 train/dev/test 扩展。

新增 eval case 时必须能追溯到真实手册证据。`evidence.quote` 应来自已解析 chunk、`inspect_chunks.py` 输出或手册页面文本，不允许凭汽车常识编写。

## Retrieval Evaluation

单模式评测：

```bash
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --retrieval-mode dense --top-k 5
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --retrieval-mode bm25 --top-k 5
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --retrieval-mode hybrid --top-k 5
```

对比三种检索模式：

```bash
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --all-modes --top-k 5
```

启用 metadata-aware context selection 后评测最终上下文：

```bash
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --retrieval-mode hybrid --top-k 5 --use-context-selection
```

快速调试：

```bash
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --all-modes --top-k 5 --limit 5
```

过滤样例：

```bash
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --retrieval-mode hybrid --category warning_notice
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --retrieval-mode hybrid --intent-type specific_operation
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --retrieval-mode hybrid --split dev
```

输出报告：

```bash
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --all-modes --top-k 5 --output reports/evaluation/v3_0_2_retrieval.md
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --all-modes --top-k 5 --output reports/evaluation/v3_0_2_retrieval.json
python scripts/evaluate_retrieval.py --dataset data/eval/manual_eval_set.jsonl --all-modes --top-k 5 --output reports/evaluation/v3_0_2_retrieval.csv
```

`reports/evaluation/` 下的运行报告通常是本地生成结果，不建议提交大体积报告。

## Metrics

第一版指标使用简单可复现规则，不使用 LLM-as-judge。

- `page_hit@k`：top-k 中是否命中 `expected_pages`。
- `expected_section_hit@k`：top-k 中是否命中 `expected_sections`。
- `acceptable_section_hit@k`：top-k 中是否命中 `expected_sections` 或 `acceptable_sections`。
- `content_type_hit@k`：top-k 中是否命中 `expected_content_types`；没有期望类型时记为 N/A。
- `any_term_hit@k`：top-k 文本是否命中任一 `must_contain_terms`。
- `all_terms_hit@k`：top-k 文本是否覆盖全部 `must_contain_terms`。
- `term_coverage_ratio@k`：top-k 文本覆盖 `must_contain_terms` 的比例。
- `evidence_hit@k`：比页码命中更严格，综合 evidence quote、section、page、content_type 和 must terms。
- `mrr`：基于首次 evidence hit 的 reciprocal rank。
- `average_first_hit_rank`：首次 evidence hit 的 rank。
- `noise_rate@k`：top-k 中 TOC/noise chunk 占比。
- `duplicate_chunk_id_rate@k`：chunk_id 重复比例。
- `same_page_duplicate_rate@k`：同 source/page/normalized text 重复比例。
- `cross_page_repeated_content_rate@k`：跨页重复文本比例；该指标不一定表示错误，只用于诊断。
- `final_context_hit`：启用 context selection 时，最终上下文是否存在 evidence hit。

## Smoke Tests vs Eval Dataset

当前四个 smoke tests 只用于回归检查：

1. 如何正确使用安全带？
2. 胎压报警后应该怎么办？
3. 车辆涉水驾驶后需要检查什么？
4. 充电时有哪些安全注意事项？

通过 smoke tests 不代表系统整体效果好；某个 smoke test 失败，也不自动意味着应该新增规则。后续检索优化、metadata selection 调整、tokenizer 改动、V3.1 rerank 或 query rewrite，都应先通过 evaluation runner 做量化对比。

不要根据单个 eval case 直接新增规则。新增规则必须解决通用问题，并且可解释、可 debug、可评估。

## 评测集局限和解读注意事项

当前 `manual_eval_set.jsonl` 是第一版 `dev` set，用于建立可复现的比较基线，不应视为最终冻结的 `test` set。解读报告时需要注意：

- `section_hit` 依赖 chunk metadata 质量。当前 parser 仍可能产生 section 缺失或解析偏差；遇到此类样例时，应结合 `page_hit`、`evidence_hit` 和 `term_coverage_ratio` 判断，不应只看 `section_hit`。
- `content_type_hit` 依赖 parser 对 `warning`、`caution`、`procedure` 等类型的标注质量，只能作为辅助指标。
- `any_term_hit` 只表示至少命中一个关键词，容易虚高，不能单独代表证据命中。应优先结合 `evidence_hit`、`all_terms_hit` 和 `term_coverage_ratio` 解读。
- `evidence.quote` 应尽量具体，并能追溯到真实 indexed chunk。避免使用过短、过泛或依赖图标语义的片段。
- 当前项目是纯文本 RAG。默认不将需要图标识别、图片理解或其他多模态能力的问题纳入普通评测。
- 不得根据单个 eval case 的失败直接修改 retrieval 规则。后续优化必须先确认问题是否具有通用性，再通过完整 dev set 和消融对比验证。

## dataset changelog
删除 seatbelt_after_collision_warning_001：该样例的 evidence 标注置信度不足，可能导致误判检索失败，因此暂时从 V3.0.2 eval set 中移除。