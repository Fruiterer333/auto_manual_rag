# Evaluation Report Index

本目录保留评测方法、冻结结果和受控实验证据。主 README 只展示少量关键指标；需要复核数据来源、配置、失败样例或历史决策时，再进入对应报告。

当前 retrieval benchmark 和 answer diagnostic set 都来自单本汽车用户手册，不能解释为 production accuracy 或跨车型能力。

## Current / Final

- [V4.8 Final System Evaluation](v4_8_final_system_evaluation.md)：当前 Resume-Ready 技术配置、最终 retrieval verification、12-case answer diagnostic 结果和 known limitations。
- [V4.8 Answer Evaluation](v4_8_final_system_answer_eval_20260903_001.md)：最终 12-case Exact Prompt Evidence、raw/final answer、citations 和自动诊断。
- [V3.5 Retrieval Benchmark Summary](v3_5_retrieval_benchmark_summary.md)：69 records / 68 active 的冻结 retrieval benchmark 定义与指标。
- [V3.5 Frozen Hybrid No-Rerank](v3_5_frozen_hybrid_no_rerank.json)：当前默认 retrieval mode 的机器可读结果。
- [V3.5 Frozen Hybrid + Rerank](v3_5_frozen_hybrid_rerank.json)：optional rerank 的机器可读结果。
- [V3.5 Frozen Rerank Comparison](v3_5_frozen_rerank_comparison.md)：rerank 排序收益、case regressions 和成本边界。

## Answer Quality and Model Selection

- [V4.5 Human Adjudication Summary](v4_5_c_human_adjudication_summary.md)：V4.4 historical baseline 的人工评分和 failure taxonomy。
- [V4.5 Generation Reproducibility](v4_5_1_generation_reproducibility.md)：generation parameters 与重复运行审计边界。
- [V4.7 Answer Model Selection](v4_7_answer_model_selection.md)：`qwen2.5:7b`、`qwen3.5:9b`、`gemma3:12b` 的受控比较与最终选择。
- [V4.7 Selected Model Stability](v4_7_selected_model_generation_stability.md)：选定模型 4 cases x 3 runs 的 exact-output stability verification。

## Methodology / Governance

- [Evaluation Guide](../../docs/evaluation.md)：dataset、指标、claim boundary 和运行方法。
- [V4.3 Evaluation Semantics Freeze](v4_3_answer_evaluation_semantics_freeze.md)：answer evaluator 的冻结语义。
- [V3.5 Retrieval Reference Audit](v3_5_retrieval_reference_audit.md)：benchmark/index 对齐和 provenance 检查。
- [V3.5 Recalibration Audit](v3.5_manual_eval_recalibration_audit.md)：chunk strategy 变化后的逐 case recalibration。

## Key Controlled Experiment

- [V4.6 Failure-to-Intervention Mapping](v4_6_a_failure_to_intervention_mapping.md)：从人工 failure taxonomy 到单变量实验设计。
- [V4.6 Condition Preservation Experiment](v4_6_b_condition_preservation_experiment.md)：未达到目标的 Prompt treatment，最终结论为 `REJECT`，稳定 Prompt 未改变。

## Historical Reports

其余 `v3_0_*`、`v3_1_*`、`v3_2_*`、pre-freeze `v3_5_*` 和早期 V4 reports 是开发过程记录。它们可能使用旧 benchmark、旧模型或旧 generation defaults，不能替代上述 Current / Final artifacts。

历史报告继续保留，以便解释架构演进和负实验；不会在主 README 中逐一展示，也不应被误读为当前 baseline。
