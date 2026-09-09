# Final Evaluation Report

本目录只保留直接支持公开评测结论的最终 artifacts。指标来自单手册 dev benchmark，用于验证 retrieval ranking 和 answer traceability，不代表 production accuracy。

## Retrieval

Retrieval dataset 包含 69 条 records，其中 68 条 active、1 条 excluded。

| Configuration | Hit@1 | Hit@3 | Hit@5 | MRR |
| --- | ---: | ---: | ---: | ---: |
| Hybrid | 0.6618 | 0.9265 | 0.9706 | 0.7922 |
| Hybrid + Reranker | 0.8676 | 0.9853 | 1.0000 | 0.9277 |

- [Benchmark summary](v3_5_retrieval_benchmark_summary.md)
- [Hybrid machine-readable result](v3_5_frozen_hybrid_no_rerank.json)
- [Hybrid + reranker machine-readable result](v3_5_frozen_hybrid_rerank.json)
- [Reranker comparison](v3_5_frozen_rerank_comparison.md)

## Answer and Generation

Answer evaluation 使用 12-case dev diagnostic set，并保存 Exact Prompt Evidence、raw/final answer、citations 和 runtime metadata。它主要用于分析 groundedness、correctness、completeness 与 condition handling，不作为公开准确率指标。

- [Final answer evaluation artifact](v4_8_final_system_answer_eval_20260903_001.json)
- [Selected model repeated-run stability](v4_7_selected_model_generation_stability.json)

## Methodology

Dataset 语义、consistency validation、指标定义和运行命令见 [Evaluation Methodology](../../docs/evaluation.md)。
