# V3.1 Rerank Evaluation Summary

本文档沉淀 `auto-manual-rag` 项目 V3.1 rerank 阶段的设计、实现和评测结论，用于技术复盘、后续迭代和面试讲解。

## 1. Background

V3.0.3 cross-mode diagnostics 显示，当前 hybrid retrieval 的 top-5 evidence recall 已经较好：正确 evidence 多数能够进入 top-5。主要问题不再是候选召回不足，而是候选 chunk 之间的 top-1 排序质量。

hybrid retrieval 通过 RRF 融合 dense 和 BM25 的排名，可以兼顾语义召回与关键词召回，但在部分 case 上也可能受到单侧偏差影响。例如，同一主题下的功能说明、操作步骤和安全提醒可能包含相近词汇，RRF 无法直接判断哪个 chunk 更符合用户的具体意图。

`context selection` 只负责轻量上下文整理、长度控制、去重和 citation metadata 保留，不是 reranker。继续向 context selection 叠加手写 bonus、penalty 或 case-specific 规则会模糊职责边界，并增加过拟合风险。

因此，V3.1 引入 cross-encoder rerank 作为 precision-ranking module。这个决策来自 evaluation diagnostics，而不是为了堆功能。

## 2. Rerank Design

```text
User Query
  -> Dense / BM25 / Hybrid Retrieval
  -> Hygiene Filter / Dedup
  -> Cross-Encoder Rerank
  -> Context Selection
  -> Prompt Construction
  -> LLM Answer
```

职责边界：

- **Retrieval**：召回候选 chunk。当前支持 dense、BM25 和 hybrid retrieval。
- **Hygiene Filter / Dedup**：过滤 TOC、noise 和重复内容，减少无效候选。
- **Cross-Encoder Rerank**：对 query-chunk pair 做 relevance 精排，不扩大召回范围。
- **Context Selection**：整理 rerank 后的候选，控制上下文长度，并保留 citation metadata。
- **LLM Generation**：基于最终 context 生成回答，不负责修复 retrieval 或 rerank 失败。

rerank 不替代 hybrid retrieval，也不替代 context selection。它位于候选召回和上下文整理之间，只处理候选排序。

## 3. Implementation Milestones

| Version | Milestone | Summary |
| --- | --- | --- |
| V3.1.0 | Reranker interface and Noop baseline | Added `BaseReranker`, `NoopReranker`, config skeleton, and pipeline hook. |
| V3.1.1 | Cross-Encoder baseline | Added local `CrossEncoderReranker` with lazy loading and rerank metadata. |
| V3.1.2 | Rerank on/off comparison | Added JSON-based comparison script for no-rerank vs rerank evaluation. |

默认配置：

```env
ENABLE_RERANK=false
```

保持默认关闭的原因：

- 保证现有稳定链路不被额外模型推理影响；
- 避免在评测集仍较小时改变默认行为；
- rerank 会增加本地推理成本和响应延迟；
- 启用策略应基于更大评测集和 latency review，而不是少量样例。

## 4. Evaluation Setup

- Dataset：`data/eval/manual_eval_set.jsonl`
- Case count：29
- Retrieval mode：`hybrid`
- Baseline：hybrid without rerank
- Experiment：hybrid + `BAAI/bge-reranker-base`
- Top-k：5
- Comparison script：`scripts/compare_rerank_evaluation.py`

This is a development evaluation set, not a final benchmark.

当前 29 条样例是开发评测集，用于指导迭代和比较方案，不应被视为最终 benchmark。单个 case 的结果只能用于定位问题，不能直接成为新增规则的依据。

## 5. Overall Results

| Metric | No rerank | With rerank | Delta |
| --- | ---: | ---: | ---: |
| `evidence_hit@1` | 0.7931 | 0.8966 | +0.1034 |
| `MRR` | 0.8908 | 0.9483 | +0.0575 |
| `evidence_hit@5` | 1.0000 | 1.0000 | +0.0000 |

结果解读：

- `evidence_hit@1` 提升，说明 rerank 改善了 top-1 排序。
- `MRR` 提升，说明正确 evidence 的整体排名更靠前。
- `evidence_hit@5` 没有下降，说明 rerank 没有破坏 top-5 evidence recall。
- 结果符合 rerank 的目标：重排已经召回的候选，而不是扩大召回。

cross-encoder rerank 在当前 dev set 上显示出明确的正向效果，但这不是最终 benchmark，也不代表排序问题已经被彻底解决。

## 6. Case Movement Analysis

| Item | Count |
| --- | ---: |
| `improved_cases` | 4 |
| `regressed_cases` | 0 |
| `unchanged_cases` | 25 |
| `newly_top1_hit` | 3 |
| `lost_top1_hit` | 0 |
| `evidence_hit@5_regressions` | 0 |

指标解释：

- `improved_cases`：rerank 让正确 evidence 的 rank 更靠前。
- `newly_top1_hit`：正确 evidence 原本不是 top-1，rerank 后变为 top-1。
- `regressed_cases = 0`：当前 dev set 中没有观察到 case-level 排名退化。
- `evidence_hit@5_regressions = 0`：当前 dev set 中没有丢失 top-5 evidence。

这些结果说明 rerank 在当前 dev set 上显示出正向效果，但不能据此推断所有问题类型都能受益。

## 7. Improved Cases

| Case ID | Interpretation |
| --- | --- |
| `seatbelt_fastening_001` | Rerank moved the result from a generic seatbelt section to the more specific fastening section. |
| `tire_repair_after_limits_001` | Rerank improved ranking for a parameter/limit question. |
| `tire_repair_before_001` | Rerank improved ordering among closely related tire repair chunks. |
| `front_hood_open_001` | Rerank improved a procedure-oriented hood opening case. |

`seatbelt_fastening_001` 是较直观的例子：

- baseline top-1 section：`安全带作用`
- rerank top-1 section：`系紧安全带`

这说明 cross-encoder 更容易判断“如何系紧安全带”与具体操作步骤之间的相关性。其他 improved cases 也体现了排序改善，但部分 chunk 的 section metadata 不完整，因此这里只做概括性解读。

## 8. Remaining Non-Top1 Cases

仍未解决的 non-top1 cases：

- `epb_enable_release_001`
- `front_hood_close_warning_001`

`epb_enable_release_001`：

- baseline 和 rerank 后仍未达到 top-1；
- top-1 仍可能落在 `手动紧急制动` 等相近章节；
- 说明 rerank 对语义高度接近的章节仍可能区分不足。

`front_hood_close_warning_001`：

- rerank 后仍未达到 top-1；
- 可能与 chunk 边界或 section metadata 缺失有关；
- 需要后续人工 review，不应为单个 case 编写特例规则。

这些 failure cases 应作为诊断输入，而不是 query-specific 补丁的依据。

## 9. Latency Cost

| Metric | No rerank | With rerank | Delta |
| --- | ---: | ---: | ---: |
| `elapsed_seconds` | 18.5248 | 33.0765 | +14.5517 |
| `average_seconds_per_case` | 0.6388 | 1.1406 | +0.5018 |

rerank 增加了本地推理成本。当前评测总耗时约从 18.52 秒增加到 33.08 秒，平均每条 case 的耗时约从 0.64 秒增加到 1.14 秒。

这体现了效果收益与成本之间的权衡：rerank 改善了排序质量，但延迟也随之上升。因此，当前不应默认开启 rerank。后续可以继续评估 batch inference、device optimization、`top_n` tuning 和更细粒度 latency reporting。

## 10. Engineering Decision

当前工程决策：

- Keep rerank as an optional precision-ranking module.
- Keep `ENABLE_RERANK=false` by default.
- Do not replace hybrid retrieval with rerank.
- Do not use rerank as a substitute for retrieval evaluation.
- Do not tune rules based on a few cases.
- Expand the evaluation set before considering default enabling.

cross-encoder rerank 已经在当前 dev set 上初步验证有效，但尚未证明适合默认开启。继续默认关闭，可以保护现有链路稳定性，并保持延迟可控。

## 11. Limitations

- 当前 eval set 只有 29 条。
- 当前结果来自 dev set，不是 final benchmark。
- 尚未比较多个 reranker 模型。
- 尚未系统评估 MPS、CPU 和 batch size 的速度差异。
- latency 目前主要基于整体运行时间和平均每 case 时间。
- 部分 section metadata 仍然缺失或存在解析偏差。
- 仍有少数 case 未被 rerank 解决。

## 12. Next Steps

1. Expand eval set from 29 to 50+ cases.
2. Re-run hybrid no-rerank vs hybrid + rerank comparison.
3. Add more latency metrics, such as avg / median / p95 rerank latency.
4. Review remaining non-top1 cases.
5. Consider model comparison only after eval set expansion.
6. Keep rerank disabled by default until larger evaluation confirms benefit.
