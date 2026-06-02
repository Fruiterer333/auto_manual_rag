# Rerank Evaluation Summary

## 1. Purpose

本文档总结 V3.2 阶段在清洗后的 text-only dev evaluation set 上进行的 hybrid baseline 与 cross-encoder rerank 对比结果。

这是 development evaluation，不是 final benchmark。当前目标是判断 rerank 是否能改善 top-1 evidence ranking。本文档不评估 LLM answer generation，也不评估依赖图标、按钮示意图、编号图例或视觉版面的 multimodal cases。

## 2. Dataset

- dataset path：`data/eval/manual_eval_set.jsonl`
- case count：69
- split：`dev`
- scope：text-only automotive manual QA

当前 eval set 已删除或改写明显依赖视觉信息的 cases，只保留能够由文字 evidence 支撑的问题。它仍然来自单一汽车用户手册语料，不是 final benchmark，也不能代表所有车型、品牌或汽车手册问题。

## 3. Compared Runs

Baseline：

- `retrieval_mode=hybrid`
- `rerank_enabled=false`
- `top_k=5`

Experiment：

- `retrieval_mode=hybrid`
- `rerank_enabled=true`
- `rerank_model_name=BAAI/bge-reranker-base`
- `rerank_top_n=10`
- `rerank_output_top_k=5`
- `top_k=5`
- `device=auto`

rerank 位于 hygiene filter / dedup 之后、context selection 之前。它不扩大原始 retrieval recall，只重排候选 chunk。默认配置仍保持：

```env
ENABLE_RERANK=false
```

## 4. Overall Results

| metric | baseline | rerank | delta |
| --- | ---: | ---: | ---: |
| `evidence_hit@1` | 0.7681 | 0.9130 | +0.1449 |
| `evidence_hit@3` | 1.0000 | 1.0000 | +0.0000 |
| `evidence_hit@5` | 1.0000 | 1.0000 | +0.0000 |
| `mrr` | 0.8792 | 0.9541 | +0.0749 |
| `average_first_hit_rank` | 1.2609 | 1.1014 | -0.1594 |
| `page_hit@1` | 0.7971 | 0.9130 | +0.1159 |
| `elapsed_seconds` | 23.7179 | 42.8940 | +19.1761 |
| `average_seconds_per_case` | 0.3437 | 0.6217 | +0.2780 |

结果解读：

- `evidence_hit@1` 和 `mrr` 明显提升。
- `evidence_hit@3` / `evidence_hit@5` 保持不变。
- `average_first_hit_rank` 越低越好。
- `elapsed_seconds` 越高表示本地推理成本更高。

## 5. Case Movement Summary

| item | count |
| --- | ---: |
| `improved_cases` | 11 |
| `regressed_cases` | 1 |
| `unchanged_cases` | 57 |
| `newly_top1_hit` | 10 |
| `lost_top1_hit` | 0 |
| `evidence_hit@5_regressions` | 0 |

rerank 将多个原本位于 rank 2 / rank 3 的正确 evidence 提升到 rank 1。当前没有 `lost_top1_hit`，也没有 top-5 evidence recall regression。唯一 regression 仍在 top-5 内，不影响 `evidence_hit@5`。

## 6. Interpretation

当前 hybrid retrieval 已能在 top-5 中召回正确 evidence。主要问题不是候选 recall，而是 rank ordering。

cross-encoder rerank 有助于处理相似章节、同页多主题和关键词重叠导致的排序问题，在当前 69 条 text-only dev set 上显著提升 top-1 evidence 排序质量。这支持将 rerank 保留为核心 optional ranking module，但不代表 rerank 已经解决所有检索问题。

## 7. Latency Cost

- 总耗时从约 `23.72s` 增加到 `42.89s`。
- 平均每 case 从约 `0.34s` 增加到 `0.62s`。
- latency cost 约为 `1.81x`。

因此，当前不建议默认开启 rerank。对于本地评测、分析和可选高质量问答模式，这一成本可以接受；对于实时 API，仍需要进一步做 latency optimization。

## 8. Current Decision

当前决策：保留 cross-encoder rerank 作为可选增强模块，但暂不默认开启。默认链路仍保持 hybrid retrieval，不改变现有稳定行为。

- 保留 cross-encoder rerank 作为可选增强模块；
- ENABLE_RERANK=false 仍为默认配置；
- 暂不改变默认 retrieval 行为；
- rerank 当前主要用于评测分析、效果对比，以及可选的高精度检索模式；
- 不建议现在默认开启 rerank，原因包括：数据集仍是 69 条 text-only dev cases、仍有少量 regressed / unchanged non-top1 cases、latency 增加约 1.81x，且尚未完成更大规模评测和参数对照实验。

## 9. Remaining Issues

- eval set 仍是单一汽车手册 dev set。
- 当前只有 69 条 text-only dev cases，不是 final benchmark。
- 仍有 1 个 regressed case。
- 仍有若干 unchanged non-top1 cases。
- section metadata 仍存在缺失或错位。
- context selection 仍是轻量模块，后续需要瘦身或重新定位。
- visual-dependent manual QA 仍未处理。
- latency 仍需评估和优化。
- 尚未比较 `BAAI/bge-reranker-base` 与 `BAAI/bge-reranker-v2-m3`。
- 尚未系统评估 `rerank_top_n=10` / `20` 的差异。
- 尚未进行 answer-level evaluation。

## 10. Next Steps

- 对 regressed cases 和 unchanged non-top1 cases 做 failure case review； 
- 只有在新增样例能扩大覆盖面时，才继续补充 text-only dev cases； 
- 对比 rerank_top_n = 10 和 rerank_top_n = 20 的效果与耗时； 
- 可选对比 BAAI/bge-reranker-base 与 BAAI/bge-reranker-v2-m3； 
- 如果后续将 rerank 面向用户请求开放，需要补充更细的 latency metrics； 
- 在完成 failure case review 前，不引入 query rewrite； 
- 在完成更大范围评测、参数对照和延迟评估前，不默认开启 rerank； 
- 继续关注 chunking、section metadata、context selection 和冗余模块瘦身问题。
