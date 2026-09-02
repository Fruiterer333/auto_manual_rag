# V3.5 Frozen Retrieval Rerank Comparison

- generated_at: 2026-09-01T23:38:53
- baseline: `reports/evaluation/v3_5_frozen_hybrid_no_rerank.json`
- experiment: `reports/evaluation/v3_5_frozen_hybrid_rerank.json`
- benchmark_status: frozen
- chunking_index_version: V3.5
- total_records: 69
- active_case_count: 68
- excluded_case_count: 1 (`parking_detection_range_001`)
- adjudication_status: complete
- wiper_equivalent_gold_chunks: `32e9fad8-2056-5ffd-99b5-74871d62d66a`, `62db6352-468d-5c6d-a527-c13f334becb1`

> This report uses the frozen V3.5 retrieval benchmark after gold evidence adjudication. Differences from legacy or pre-freeze reports may reflect corrected evaluation labels rather than production retrieval changes.

## 1. Run Metadata

| item | baseline | experiment |
| --- | --- | --- |
| retrieval_mode | hybrid | hybrid |
| rerank_enabled | false | true |
| rerank_model_name | N/A | BAAI/bge-reranker-base |
| top_k | 5 | 5 |
| case_count | 68 | 68 |
| elapsed_seconds | 21.1150 | 42.9571 |

## 2. Overall Metric Delta

| metric | baseline | experiment | delta |
| --- | ---: | ---: | ---: |
| evidence_hit@1 | 0.6618 | 0.8676 | +0.2059 |
| evidence_hit@3 | 0.9265 | 0.9853 | +0.0588 |
| evidence_hit@5 | 0.9706 | 1.0000 | +0.0294 |
| mrr | 0.7922 | 0.9277 | +0.1355 |
| average_first_hit_rank | 1.5000 | 1.1765 | -0.3235 |
| page_hit@1 | 0.8676 | 0.9265 | +0.0588 |
| term_coverage_ratio@1 | 0.7343 | 0.8652 | +0.1309 |
| final_context_hit | N/A | N/A | N/A |
| elapsed_seconds | 21.1150 | 42.9571 | +21.8421 |

Delta interpretation: larger is better for evidence hit, MRR, page hit, and term coverage. Smaller is better for average first hit rank. Larger elapsed time means higher cost.

## 3. Decision Summary

Rerank improved top-1 ranking quality while preserving top-5 evidence recall.

## 4. Case Movement Summary

| item | count |
| --- | ---: |
| improved_cases | 19 |
| regressed_cases | 3 |
| unchanged_cases | 46 |
| newly_top1_hit | 16 |
| lost_top1_hit | 2 |
| evidence_hit@5_regressions | 0 |

## 5. Improved Cases

| case_id | category | intent_type | baseline_rank | experiment_rank | rank_delta | baseline_top1_page | experiment_top1_page | baseline_top1_section | experiment_top1_section |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| keyless_entry_lock_001 | procedure | specific_operation | 4 | 1 | 3 | 44 | 43 | 无钥匙进入系统 | 无钥匙进入系统 |
| keyless_entry_unlock_001 | procedure | specific_operation | 3 | 1 | 2 | 44 | 43 | 无钥匙进入系统 | 无钥匙进入系统 |
| parking_emergency_brake_fault_001 | alarm_handling | state_explanation | 3 | 1 | 2 | 228 | 76 | 泊车紧急制动 | 指示灯和警告灯 |
| remote_key_start_001 | procedure | specific_operation | 3 | 1 | 2 | 143 | 143 | 通过遥控钥匙启动车辆 | 通过遥控钥匙启动车辆 |
| apa_exit_conditions_001 | warning_notice | safety_notice | 2 | 1 | 1 | 230 | 232 | 全自动泊车 | 全自动泊车 |
| autohold_explanation_001 | explanation | concept_explanation | 2 | 1 | 1 | 159 | 159 | 自动驻车系统 | 自动驻车系统 |
| automatic_wiper_sensor_001 | explanation | concept_explanation | 2 | 1 | 1 | 63 | 63 | 前雨刮和洗涤器 | 前雨刮和洗涤器 |
| front_hood_close_warning_001 | warning_notice | safety_notice | 2 | 1 | 1 | 308 | 308 | 关闭前机舱盖 | 关闭前机舱盖 |
| front_hood_open_001 | procedure | specific_operation | 2 | 1 | 1 | 311 | 307 | 添加洗涤液 | 打开前机舱盖 |
| fuse_box_location_001 | location_query | location_query | 2 | 1 | 1 | 306 | 307 | 更换保险丝 | 更换保险丝 |
| lock_auto_window_close_001 | explanation | state_explanation | 2 | 1 | 1 | 108 | 108 | 打开/关闭车窗 | 打开/关闭车窗 |
| seatbelt_fastening_001 | procedure | specific_operation | 2 | 1 | 1 | 101 | 101 | 使用安全带 | 使用安全带 |
| slope_parking_warning_001 | warning_notice | safety_notice | 2 | 1 | 1 | 166 | 166 | 斜坡驻车 | 斜坡驻车 |
| tire_pressure_label_001 | parameter_query | location_and_parameter | 2 | 1 | 1 | 62 | 314 | 胎压监测系统 | 胎压标签 |
| vin_location_001 | location_query | location_query | 2 | 1 | 1 | 331 | 347 | 道路救援求助服务指导 | 车辆标识 |
| abs_fault_handling_001 | alarm_handling | alarm_handling | N/A | 1 | N/A | 157 | 157 | 制动防抱死系统 | 制动防抱死系统 |
| fuel_safety_001 | warning_notice | safety_notice | 5 | 2 | 3 | 162 | 162 | 加油 | 加油 |
| seatbelt_usage_001 | procedure | broad_usage_guidance | 4 | 2 | 2 | 99 | 99 | 安全带 | 安全带 |
| onboard_charging_steps_001 | procedure | specific_operation | N/A | 2 | N/A | 295 | 290 | 随车设备快速充电 | 车载充电设备充电 |

## 6. Regressed Cases

| case_id | category | intent_type | baseline_rank | experiment_rank | rank_delta | baseline_top1_page | experiment_top1_page | baseline_top1_section | experiment_top1_section |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| brake_warning_lights_001 | alarm_handling | state_explanation | 1 | 2 | -1 | 155 | 155 | 制动系统 | 转向助力系统 |
| tire_pressure_alarm_001 | alarm_handling | alarm_handling | 1 | 2 | -1 | 62 | 62 | 胎压监测系统 | 胎压监测系统 |
| high_voltage_label_001 | warning_notice | forbidden_condition | 3 | 4 | -1 | 287 | 304 | 高压警告标签 | 保养和维护动力电池 |

## 7. Unchanged Non-Top1 Cases

| case_id | category | intent_type | baseline_rank | experiment_rank | baseline_top1_section | experiment_top1_section |
| --- | --- | --- | ---: | ---: | --- | --- |
| epb_enable_release_001 | procedure | specific_operation | 2 | 2 | 电子驻车制动（EPB） | 电子驻车制动（EPB） |
| pressure_wash_warning_001 | warning_notice | safety_notice | 2 | 2 | 清洁车辆 | 清洁车辆 |
| rpa_safety_001 | warning_notice | safety_notice | 3 | 3 | 遥控泊车 | 遥控泊车 |

## 8. Category Delta

| category | case_count | evidence_hit@1_baseline | evidence_hit@1_experiment | evidence_hit@1_delta | mrr_baseline | mrr_experiment | mrr_delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 7 | 0.7143 | 0.7143 | 0.0000 | 0.7619 | 0.8571 | 0.0952 |
| explanation | 14 | 0.7857 | 1.0000 | 0.2143 | 0.8929 | 1.0000 | 0.1071 |
| location_query | 3 | 0.3333 | 1.0000 | 0.6667 | 0.6667 | 1.0000 | 0.3333 |
| maintenance_check | 4 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| parameter_query | 5 | 0.8000 | 1.0000 | 0.2000 | 0.9000 | 1.0000 | 0.1000 |
| procedure | 19 | 0.5789 | 0.8421 | 0.2632 | 0.7193 | 0.9211 | 0.2018 |
| warning_notice | 16 | 0.5625 | 0.7500 | 0.1875 | 0.7417 | 0.8490 | 0.1073 |

Categories with very small case counts should be treated as directional signals only.

## 9. Intent Type Delta

| intent_type | case_count | evidence_hit@1_baseline | evidence_hit@1_experiment | evidence_hit@1_delta | mrr_baseline | mrr_experiment | mrr_delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 2 | 0.5000 | 0.5000 | 0.0000 | 0.5000 | 0.7500 | 0.2500 |
| broad_usage_guidance | 2 | 0.5000 | 0.5000 | 0.0000 | 0.6250 | 0.7500 | 0.1250 |
| concept_explanation | 9 | 0.7778 | 1.0000 | 0.2222 | 0.8889 | 1.0000 | 0.1111 |
| forbidden_condition | 4 | 0.7500 | 0.7500 | 0.0000 | 0.8333 | 0.8125 | -0.0208 |
| limit_parameter | 3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| location_and_operation | 1 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| location_and_parameter | 2 | 0.5000 | 1.0000 | 0.5000 | 0.7500 | 1.0000 | 0.2500 |
| location_query | 3 | 0.3333 | 1.0000 | 0.6667 | 0.6667 | 1.0000 | 0.3333 |
| maintenance_guidance | 4 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| safety_notice | 12 | 0.5000 | 0.7500 | 0.2500 | 0.7111 | 0.8611 | 0.1500 |
| specific_operation | 16 | 0.5625 | 0.8750 | 0.3125 | 0.7135 | 0.9375 | 0.2240 |
| state_explanation | 10 | 0.8000 | 0.9000 | 0.1000 | 0.8833 | 0.9500 | 0.0667 |

Intent types with very small case counts should be treated as directional signals only.

## 10. Latency and Cost

| metric | baseline | experiment | delta | ratio |
| --- | ---: | ---: | ---: | ---: |
| elapsed_seconds | 21.1150 | 42.9571 | +21.8421 | 2.03x |
| average_seconds_per_case | 0.3105 | 0.6317 | +0.3212 | 2.03x |

Rerank may improve ranking quality while increasing inference cost. This baseline should remain optional until broader evaluation and latency review are complete.

## 11. Recommendation

Keep rerank as an optional feature; do not enable it by default yet. Expand the evaluation set before changing default behavior, and continue latency optimization and case-level review.
