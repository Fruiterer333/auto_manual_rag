# Retrieval Evaluation Methodology

本项目的 retrieval evaluation 用于可复现地比较 dense、BM25、hybrid 和 optional rerank，不用于通过少量 case 反向调规则。当前正式基线是与 V3.5 chunk/index 对齐并完成 gold adjudication 的 frozen retrieval benchmark。

早期 V3.0.2 建立了 evaluation framework；后续 V3.2-V3.5 扩展数据集、修复 chunk hierarchy，并完成 benchmark recalibration、consistency validation、failure review 和 freeze。历史结果继续保留，但必须与当前 frozen baseline 区分。

## Retrieval Benchmark Purpose and Unit

当前 benchmark 的评测单位是 chunk-level retrieval evidence，不是 answer semantic similarity：

- 每条 active case 定义一个或多个能独立支撑问题的 gold chunks；
- `evidence_hit@k` 判断 top-k 是否命中 gold evidence；
- benchmark 不使用 retriever 当前排名反向定义 gold；
- Answer Evaluation 已在 V4 建立独立 provenance、semantics freeze、formal historical baseline 和 human adjudication；其结论仍不得混入 retrieval 指标或反向改写冻结的 V3.5 gold evidence。

Gold chunk 与 chunk strategy 版本耦合。parser、splitter、heading text、boundary 或 deterministic chunk ID 发生实质变化后，旧 gold 可能失效。此时必须基于问题、原始手册事实和新 chunk 输出重新校准，不能把 stale gold 静默计为 retrieval miss。

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

当前 V3.5 dataset 状态：

| item | value |
| --- | ---: |
| total records | 69 |
| active cases | 68 |
| excluded cases | 1 |
| benchmark evidence | 99 |
| pending human review | 0 |
| validation issues | 0 |

`parking_detection_range_001` 保留在 JSONL 中并设置 `excluded=true`。其所需表格数值未被当前 text-only chunk corpus 表示，因此属于 parser/table extraction coverage gap，不是 retrieval failure，也不进入 Hit@k / MRR denominator。

Multi-gold semantics：

- 多个 independently sufficient chunks 可同时作为 gold；
- evaluator 使用 ANY_OF，命中任意 gold 即算 evidence hit；
- MRR 使用排名最高的 gold chunk；
- 当前明确的 multi-gold cases 包括 `parking_emergency_brake_fault_001`、`charging_led_states_001` 和 `wiper_caution_001`；
- 真正需要多个 chunk 联合回答的 multi-hop / multi-evidence case 不应未经设计直接套用 ANY_OF。

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

## Benchmark Consistency Validation

正式 retrieval evaluation 前应先运行：

```bash
.venv/bin/python scripts/validate_retrieval_eval_set.py \
  --dataset data/eval/manual_eval_set.jsonl \
  --split dev
```

Validator 检查 active gold chunk 是否存在，以及 evidence text、page、section/subsection 等关键字段是否与当前 index 一致。Excluded case 不要求 gold 存在。发现 stale gold 时应 fail-fast，而不是继续运行并把 benchmark inconsistency 记为 retrieval miss。

触发 recalibration 的典型变化包括：

- parser hierarchy 或 heading inheritance 改变；
- subsection heading 加入 chunk text；
- chunk boundary 拆分、合并或跨页行为改变；
- chunk ID 生成输入发生变化；
- gold evidence 被证明存在多个等价 current chunks。

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

当前 `manual_eval_set.jsonl` 已冻结为 V3.5 retrieval dev benchmark，但不应视为跨手册、跨车型的最终 `test` set。解读报告时需要注意：

- `section_hit` 依赖 chunk metadata 质量。当前 parser 仍可能产生 section 缺失或解析偏差；遇到此类样例时，应结合 `page_hit`、`evidence_hit` 和 `term_coverage_ratio` 判断，不应只看 `section_hit`。
- `content_type_hit` 依赖 parser 对 `warning`、`caution`、`procedure` 等类型的标注质量，只能作为辅助指标。
- `any_term_hit` 只表示至少命中一个关键词，容易虚高，不能单独代表证据命中。应优先结合 `evidence_hit`、`all_terms_hit` 和 `term_coverage_ratio` 解读。
- `evidence.quote` 应尽量具体，并能追溯到真实 indexed chunk。避免使用过短、过泛或依赖图标语义的片段。
- 当前项目是纯文本 RAG。默认不将需要图标识别、图片理解或其他多模态能力的问题纳入普通评测。
- 不得根据单个 eval case 的失败直接修改 retrieval 规则。后续优化必须先确认问题是否具有通用性，再通过完整 dev set 和消融对比验证。

## dataset changelog
删除 seatbelt_after_collision_warning_001：该样例的 evidence 标注置信度不足，可能导致误判检索失败，因此暂时从 V3.0.2 eval set 中移除。

## V3.5 Retrieval Benchmark Freeze

V3.5 Retrieval Benchmark 已完成以下收尾步骤：

1. chunk strategy recalibration；
2. benchmark consistency validation；
3. retrieval failure review；
4. gold-equivalence adjudication；
5. final benchmark freeze。

当前冻结基准状态：

- total records：69；
- active cases：68；
- excluded cases：1；
- benchmark evidence：99；
- pending human review：0；
- validation issues：0；
- excluded case：`parking_detection_range_001`，原因是所需表格数值未被当前纯文本 chunk corpus 表示；
- chunking/index version：V3.5；
- Chroma stored chunks：1002；
- BM25 / hygiene-filtered retrieval-eligible chunks：981；
- `parking_emergency_brake_fault_001` 包含 3 个 independently sufficient equivalent gold chunks；
- `charging_led_states_001` 包含 2 个完整覆盖 8 种 LED 状态的 equivalent gold chunks；
- `wiper_caution_001` 包含 2 个 equivalent gold chunks：前雨刮和后雨刮的完整冬季使用注意事项文本。

历史结果的含义必须明确区分：

- legacy V3.5 metrics：使用 recalibration 前的旧 `manual_eval_set`，仅作为历史实验记录；
- pre-freeze recalibrated result：完成 chunk/index 对齐和重校准、但尚未接受最终 gold-equivalence 决策的结果；
- official V3.5 retrieval baseline：使用当前 69 条记录、68 条 active cases 和最终 multi-gold 标注重新计算的 frozen metrics。

冻结后的指标变化可能来自 gold 标注修正，而不一定代表 production retrieval regression 或 improvement。多 gold case 使用 ANY_OF 语义：命中任意一个已确认等价 chunk 即算 evidence hit，MRR 使用排名最高的 gold chunk。

## Legacy, Recalibrated and Frozen Results

不同报告使用不同 benchmark state，不能直接做 production regression 解释：

| benchmark state | 含义 |
| --- | --- |
| legacy / pre-recalibration | 使用旧 chunk mapping、旧 metadata 或旧 gold truth 的历史实验。 |
| recalibrated pre-freeze | 已与 V3.5 index 对齐，但尚未完成最后 gold-equivalence adjudication。 |
| frozen / official | 完成 recalibration、validation、ambiguity review 和 gold-equivalence adjudication 后的正式 V3.5 baseline。 |

Official frozen metrics：

| mode | Hit@1 | Hit@3 | Hit@5 | MRR | elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hybrid no-rerank | 0.6618 | 0.9265 | 0.9706 | 0.7922 | 21.11s |
| Hybrid + rerank | 0.8676 | 0.9853 | 1.0000 | 0.9277 | 42.96s |

Pre-freeze recalibrated → frozen：

- no-rerank Hit@1：`0.6471 -> 0.6618`，MRR：`0.7848 -> 0.7922`；
- rerank Hit@1：`0.8529 -> 0.8676`，MRR：`0.9203 -> 0.9277`；
- Hit@3 / Hit@5 不变。

这组小幅变化来自 `wiper_caution_001` equivalent-gold adjudication，不是 production retrieval improvement。Legacy → recalibrated 的较大变化主要来自 benchmark truth 修正，也不能解释为在同一 benchmark 上发生 production regression。

## Reranker Interpretation

在 frozen benchmark 上，rerank：

- 将 Hit@1 从 `45/68` 提升到 `59/68`；
- 将 Hit@5 从 `66/68` 提升到 `68/68`；
- 明显改善 ranking quality；
- 仍存在 3 个 regressed cases 和 2 个 lost-top1 cases；
- 当前代码默认仍为 `ENABLE_RERANK=false`。

Rerank 只能重排已有候选，不能修复 parser/table extraction coverage gap、stale benchmark 或缺失 evidence。当前没有证据支持继续增加 retrieval complexity，也没有依据仅凭单次运行延迟默认开启 rerank。

## Latency Measurement Limitations

Frozen reports 中的 `21.11s` 和 `42.96s` 只记录对应单次运行。模型加载、缓存、设备状态和进程生命周期都会影响结果，不能据此形成严格 latency ratio 结论。

正式 latency comparison 应至少使用：

- 同一进程和相同硬件；
- model warmup；
- 多轮重复运行；
- per-query latency；
- p50 / p95；
- 区分模型加载时间与稳态推理时间。

## Transition to Answer Evaluation

V3.5 Retrieval 阶段已经 freeze。下一主阶段是 V4 Answer Quality / Answer Evaluation：

1. refresh `answer_eval_set` provenance；
2. 将 answer evidence 与 frozen V3.5 benchmark 对齐；
3. 修复 answer evaluator 已知问题；
4. 建立正式 answer baseline；
5. 引入 groundedness、citation correctness、coverage、forbidden content 和人工评分；
6. 根据 answer failure types 做局部改进。

Retrieval frozen 不代表最终答案质量已经解决。Candidate recall 较高后，剩余问题更可能集中在 ranking、context assembly、evidence usage 和 generation，而不是需要继续堆叠 retrieval 技术。

## V4.7 Answer Model Selection 与稳定默认配置

V4.7 在 retrieval、Prompt、Prompt Evidence、context、dataset、evaluation semantics 和 application-level generation parameters 保持不变的条件下，对 `qwen2.5:7b`、`qwen3.5:9b` 和 `gemma3:12b` 做了 12-case dev diagnostic controlled comparison。三组运行的 Prompt Evidence identity/order/text 对 12/12 cases 完全一致。

最终人工选型结论为 `qwen3.5:9b`。它与 `gemma3:12b` 的 proposed quality 基本持平，均修复两个 primary condition-handling targets，但模型体积和本地离线运行 elapsed 更低。该结论只适用于当前 dev diagnostic set 和本机部署约束，不是 production accuracy 结论。

稳定默认 generation configuration：

- model：`qwen3.5:9b`；
- temperature：`0.0`；
- seed：`42`；
- stream：`false`；
- think：`false`。

集成后在 Ollama `0.33.2`、model digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` 下完成 4 cases x 3 runs 验证，Prompt Evidence identity/order/text、raw answer 和 final answer 均 exact match。该结果只证明当前固定环境的重复运行稳定性，不代表跨硬件、跨 Ollama 版本或跨 inference backend 的普适确定性。

下一阶段为 V4.8 Final System Evaluation。不得在该评测中继续扩大 Answer Model 候选集，或同时修改 Prompt、retrieval 与 context selection。
