# V3.5 Subsection Whitelist Rerank Comparison

- generated_at: 2026-06-09T18:39:14
- baseline: `/tmp/v3_5_subsection_whitelist_no_rerank.json`
- experiment: `/tmp/v3_5_subsection_whitelist_rerank.json`

## 1. Run Metadata

| item | baseline | experiment |
| --- | --- | --- |
| retrieval_mode | hybrid | hybrid |
| rerank_enabled | false | true |
| rerank_model_name | N/A | BAAI/bge-reranker-base |
| top_k | 5 | 5 |
| case_count | 69 | 69 |
| elapsed_seconds | 14.7742 | 33.6090 |

## 2. Overall Metric Delta

| metric | baseline | experiment | delta |
| --- | ---: | ---: | ---: |
| evidence_hit@1 | 0.8841 | 0.9710 | +0.0870 |
| evidence_hit@3 | 0.9855 | 1.0000 | +0.0145 |
| evidence_hit@5 | 1.0000 | 1.0000 | +0.0000 |
| mrr | 0.9353 | 0.9855 | +0.0502 |
| average_first_hit_rank | 1.1739 | 1.0290 | -0.1449 |
| page_hit@1 | 0.8551 | 0.8986 | +0.0435 |
| term_coverage_ratio@1 | 0.7237 | 0.8527 | +0.1290 |
| final_context_hit | N/A | N/A | N/A |
| elapsed_seconds | 14.7742 | 33.6090 | +18.8348 |

Delta interpretation: larger is better for evidence hit, MRR, page hit, and term coverage. Smaller is better for average first hit rank. Larger elapsed time means higher cost.

## 3. Decision Summary

Rerank improved top-1 ranking quality while preserving top-5 evidence recall.

## 4. Case Movement Summary

| item | count |
| --- | ---: |
| improved_cases | 7 |
| regressed_cases | 0 |
| unchanged_cases | 62 |
| newly_top1_hit | 6 |
| lost_top1_hit | 0 |
| evidence_hit@5_regressions | 0 |

## 5. Improved Cases

| case_id | category | intent_type | baseline_rank | experiment_rank | rank_delta | baseline_top1_page | experiment_top1_page | baseline_top1_section | experiment_top1_section |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| parking_emergency_brake_fault_001 | alarm_handling | state_explanation | 3 | 1 | 2 | 228 | 76 | 泊车紧急制动 | 指示灯和警告灯 |
| abs_fault_handling_001 | alarm_handling | alarm_handling | 2 | 1 | 1 | 157 | 157 | 制动防抱死系统 | 制动防抱死系统 |
| apa_exit_conditions_001 | warning_notice | safety_notice | 2 | 1 | 1 | 230 | 232 | 全自动泊车 | 全自动泊车 |
| automatic_wiper_sensor_001 | explanation | concept_explanation | 2 | 1 | 1 | 63 | 63 | 前雨刮和洗涤器 | 前雨刮和洗涤器 |
| front_hood_close_warning_001 | warning_notice | safety_notice | 2 | 1 | 1 | 308 | 308 | 关闭前机舱盖 | 关闭前机舱盖 |
| onboard_charging_steps_001 | procedure | specific_operation | 2 | 1 | 1 | 295 | 290 | 随车设备快速充电 | 车载充电设备充电 |
| parking_detection_range_001 | parameter_query | limit_parameter | 5 | 2 | 3 | 224 | 224 | 泊车辅助系统 | 泊车辅助系统 |

## 6. Regressed Cases

No regressed cases found.

## 7. Unchanged Non-Top1 Cases

| case_id | category | intent_type | baseline_rank | experiment_rank | baseline_top1_section | experiment_top1_section |
| --- | --- | --- | ---: | ---: | --- | --- |
| pressure_wash_warning_001 | warning_notice | safety_notice | 2 | 2 | 清洁车辆 | 清洁车辆 |

## 8. Category Delta

| category | case_count | evidence_hit@1_baseline | evidence_hit@1_experiment | evidence_hit@1_delta | mrr_baseline | mrr_experiment | mrr_delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 7 | 0.7143 | 1.0000 | 0.2857 | 0.8333 | 1.0000 | 0.1667 |
| explanation | 14 | 0.9286 | 1.0000 | 0.0714 | 0.9643 | 1.0000 | 0.0357 |
| location_query | 3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| maintenance_check | 4 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| parameter_query | 6 | 0.8333 | 0.8333 | 0.0000 | 0.8667 | 0.9167 | 0.0500 |
| procedure | 19 | 0.9474 | 1.0000 | 0.0526 | 0.9737 | 1.0000 | 0.0263 |
| warning_notice | 16 | 0.8125 | 0.9375 | 0.1250 | 0.9062 | 0.9688 | 0.0625 |

Categories with very small case counts should be treated as directional signals only.

## 9. Intent Type Delta

| intent_type | case_count | evidence_hit@1_baseline | evidence_hit@1_experiment | evidence_hit@1_delta | mrr_baseline | mrr_experiment | mrr_delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 2 | 0.5000 | 1.0000 | 0.5000 | 0.7500 | 1.0000 | 0.2500 |
| broad_usage_guidance | 2 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| concept_explanation | 9 | 0.8889 | 1.0000 | 0.1111 | 0.9444 | 1.0000 | 0.0556 |
| forbidden_condition | 4 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| limit_parameter | 4 | 0.7500 | 0.7500 | 0.0000 | 0.8000 | 0.8750 | 0.0750 |
| location_and_operation | 1 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| location_and_parameter | 2 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| location_query | 3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| maintenance_guidance | 4 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| safety_notice | 12 | 0.7500 | 0.9167 | 0.1667 | 0.8750 | 0.9583 | 0.0833 |
| specific_operation | 16 | 0.9375 | 1.0000 | 0.0625 | 0.9688 | 1.0000 | 0.0312 |
| state_explanation | 10 | 0.9000 | 1.0000 | 0.1000 | 0.9333 | 1.0000 | 0.0667 |

Intent types with very small case counts should be treated as directional signals only.

## 10. Latency and Cost

| metric | baseline | experiment | delta | ratio |
| --- | ---: | ---: | ---: | ---: |
| elapsed_seconds | 14.7742 | 33.6090 | +18.8348 | 2.27x |
| average_seconds_per_case | 0.2141 | 0.4871 | +0.2730 | 2.27x |

Rerank may improve ranking quality while increasing inference cost. This baseline should remain optional until broader evaluation and latency review are complete.

## 11. Recommendation

Keep rerank as an optional feature; do not enable it by default yet. Expand the evaluation set before changing default behavior, and continue latency optimization and case-level review.