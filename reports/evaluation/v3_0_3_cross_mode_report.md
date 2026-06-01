# Retrieval Evaluation Report

- generated_at: 2026-06-01T19:53:55
- dataset: `data/eval/manual_eval_set.jsonl`
- case_count: 29
- retrieval_modes: dense, bm25, hybrid
- top_k: 5
- use_context_selection: False
- elapsed_seconds: 15.94

## Overall Metrics

| metric | value |
| --- | ---: |
| acceptable_section_hit@1 | 0.4713 |
| acceptable_section_hit@3 | 0.6437 |
| acceptable_section_hit@5 | 0.6897 |
| all_terms_hit@1 | 0.5977 |
| all_terms_hit@3 | 0.7816 |
| all_terms_hit@5 | 0.8621 |
| any_term_hit@1 | 0.8966 |
| any_term_hit@3 | 1.0000 |
| any_term_hit@5 | 1.0000 |
| average_first_hit_rank | 1.2414 |
| case_count | 87 |
| content_type_hit@1 | 0.8621 |
| content_type_hit@3 | 0.9655 |
| content_type_hit@5 | 0.9885 |
| cross_page_repeated_content_rate@1 | 0.0000 |
| cross_page_repeated_content_rate@3 | 0.0000 |
| cross_page_repeated_content_rate@5 | 0.0092 |
| duplicate_chunk_id_rate@1 | 0.0000 |
| duplicate_chunk_id_rate@3 | 0.0000 |
| duplicate_chunk_id_rate@5 | 0.0000 |
| evidence_hit@1 | 0.8276 |
| evidence_hit@3 | 0.9885 |
| evidence_hit@5 | 1.0000 |
| expected_section_hit@1 | 0.4598 |
| expected_section_hit@3 | 0.6322 |
| expected_section_hit@5 | 0.6782 |
| first_evidence_hit_rank | 1.2414 |
| mrr | 0.9033 |
| noise_rate@1 | 0.0000 |
| noise_rate@3 | 0.0000 |
| noise_rate@5 | 0.0000 |
| page_hit@1 | 0.7931 |
| page_hit@3 | 0.9540 |
| page_hit@5 | 0.9885 |
| retrieved_count | 4.9540 |
| same_page_duplicate_rate@1 | 0.0000 |
| same_page_duplicate_rate@3 | 0.0000 |
| same_page_duplicate_rate@5 | 0.0000 |
| term_coverage_ratio@1 | 0.7063 |
| term_coverage_ratio@3 | 0.8718 |
| term_coverage_ratio@5 | 0.9379 |

## By Retrieval Mode

| retrieval_mode | case_count | evidence_hit@1 | evidence_hit@3 | evidence_hit@5 | mrr | average_first_hit_rank | expected_section_hit@5 | acceptable_section_hit@5 | any_term_hit@5 | all_terms_hit@5 | term_coverage_ratio@5 | noise_rate@5 | duplicate_chunk_id_rate@5 | same_page_duplicate_rate@5 | cross_page_repeated_content_rate@5 | final_context_hit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | 29 | 0.8621 | 0.9655 | 1.0000 | 0.9167 | 1.2414 | 0.6552 | 0.6897 | 1.0000 | 0.8276 | 0.9207 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| dense | 29 | 0.8276 | 1.0000 | 1.0000 | 0.9023 | 1.2414 | 0.6897 | 0.6897 | 1.0000 | 0.8621 | 0.9397 | 0.0000 | 0.0000 | 0.0000 | 0.0138 | N/A |
| hybrid | 29 | 0.7931 | 1.0000 | 1.0000 | 0.8908 | 1.2414 | 0.6897 | 0.6897 | 1.0000 | 0.8966 | 0.9534 | 0.0000 | 0.0000 | 0.0000 | 0.0138 | N/A |

## Cross-mode Case Comparison

| case_id | category | intent_type | dense_rank | bm25_rank | hybrid_rank | best_mode | worst_mode | dense_top1_page | bm25_top1_page | hybrid_top1_page | dense_top1_section | bm25_top1_section | hybrid_top1_section | comparison_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| front_hood_close_warning_001 | warning_notice | safety_notice | 2 | 1 | 2 | bm25 | dense,hybrid | 308 | 308 | 308 | N/A | N/A | N/A | all_hit_within_top5,hybrid_worse_than_bm25,bm25_best,section_metadata_missing |
| front_hood_open_001 | procedure | specific_operation | 3 | 1 | 3 | bm25 | dense,hybrid | 308 | 307 | 308 | N/A | 驾驶员座椅下方的保险丝盒 | N/A | all_hit_within_top5,hybrid_worse_than_bm25,bm25_best,section_metadata_missing |
| seatbelt_fastening_001 | procedure | specific_operation | 1 | 4 | 2 | dense | bm25 | 101 | 99 | 99 | 系紧安全带 | 安全带未系提醒 | 安全带作用 | all_hit_within_top5,hybrid_worse_than_dense,dense_best |
| tire_repair_after_limits_001 | parameter_query | limit_parameter | 3 | 1 | 2 | bm25 | dense | 341 | 342 | 341 | N/A | N/A | N/A | all_hit_within_top5,hybrid_worse_than_bm25,bm25_best,section_metadata_missing |
| tire_repair_before_001 | warning_notice | safety_notice | 2 | 1 | 2 | bm25 | dense,hybrid | 341 | 341 | 341 | N/A | N/A | N/A | all_hit_within_top5,hybrid_worse_than_bm25,bm25_best,section_metadata_missing |
| epb_enable_release_001 | procedure | specific_operation | 2 | 3 | 2 | dense,hybrid | bm25 | 159 | 159 | 159 | 手动紧急制动 | 手动紧急制动 | 手动紧急制动 | all_hit_within_top5,top5_hit_but_no_top1 |
| airbag_explanation_001 | explanation | concept_explanation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 102 | 103 | 103 | 安全气囊 | 安全气囊注意事项 | N/A | all_top1_hit,section_metadata_missing |
| airbag_warning_001 | forbidden_condition | forbidden_condition | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 103 | 103 | 103 | 安全气囊注意事项 | 安全气囊注意事项 | 安全气囊注意事项 | all_top1_hit |
| charging_gun_handling_001 | procedure | specific_operation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 289 | 289 | 289 | N/A | N/A | N/A | all_top1_hit,section_metadata_missing |
| charging_safety_001 | warning_notice | safety_notice | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 295 | 295 | 295 | N/A | N/A | N/A | all_top1_hit,section_metadata_missing |
| child_lock_enable_001 | procedure | state_explanation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 122 | 122 | 122 | N/A | N/A | N/A | all_top1_hit,section_metadata_missing |
| child_safety_seat_001 | usage_guidance | broad_usage_guidance | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 122 | 122 | 122 | 儿童座椅固定装置 | 儿童座椅固定装置 | 儿童座椅固定装置 | all_top1_hit |
| defrost_enable_location_001 | procedure | location_and_operation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 256 | 257 | 256 | 空调除霜/除雾 | N/A | 空调除霜/除雾 | all_top1_hit,section_metadata_missing |
| fuel_safety_001 | warning_notice | safety_notice | 1 | 2 | 1 | dense,hybrid | bm25 | 162 | 163 | 162 | N/A | N/A | N/A | all_hit_within_top5,section_metadata_missing |
| fuel_steps_001 | procedure | specific_operation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 163 | 163 | 163 | N/A | N/A | N/A | all_top1_hit,section_metadata_missing |
| high_voltage_label_001 | warning_notice | forbidden_condition | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 287 | 304 | 304 | 高压警告标签 | N/A | N/A | all_top1_hit,section_metadata_missing |
| high_voltage_state_001 | explanation | concept_explanation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 287 | 287 | 287 | 高压警告标签 | 高压警告标签 | 高压警告标签 | all_top1_hit |
| isofix_install_001 | procedure | specific_operation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 123 | 123 | 123 | 安装ISOFIX儿童安全座椅 | 安装ISOFIX儿童安全座椅 | 安装ISOFIX儿童安全座椅 | all_top1_hit |
| low_voltage_battery_maintenance_001 | maintenance_check | maintenance_guidance | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 304 | 304 | 304 | N/A | N/A | N/A | all_top1_hit,section_metadata_missing |
| onboard_charging_steps_001 | procedure | specific_operation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 289 | 298 | 289 | 车载充电设备充电 | N/A | 车载充电设备充电 | all_top1_hit,section_metadata_missing |
| seatbelt_check_001 | maintenance_check | check_procedure | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 100 | 100 | 100 | 安全带检查 | 安全带检查 | 安全带检查 | all_top1_hit |
| seatbelt_usage_001 | usage_guidance | broad_usage_guidance | 1 | 2 | 1 | dense,hybrid | bm25 | 99 | 103 | 99 | 安全带作用 | N/A | 安全带作用 | all_hit_within_top5,section_metadata_missing |
| tire_pressure_alarm_001 | alarm_handling | alarm_handling | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 62 | 62 | 62 | 胎压低报警 | 胎压低报警 | 胎压低报警 | all_top1_hit |
| tire_pressure_label_001 | parameter_query | location_and_parameter | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 314 | 62 | 314 | 胎压标签 | 胎压低报警 | 胎压标签 | all_top1_hit |
| tire_pressure_monitoring_001 | explanation | concept_explanation | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 61 | 61 | 61 | 胎压监测系统 | 胎压监测系统 | 胎压监测系统 | all_top1_hit |
| tire_repair_kit_location_001 | location_query | location_query | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 340 | 340 | 340 | N/A | N/A | N/A | all_top1_hit,section_metadata_missing |
| wading_after_check_001 | maintenance_check | post_event_checklist | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 164 | 164 | 164 | 涉水驾驶 | 涉水驾驶 | 涉水驾驶 | all_top1_hit |
| wading_before_notice_001 | warning_notice | safety_notice | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 164 | 164 | 164 | 涉水驾驶 | 涉水驾驶 | 涉水驾驶 | all_top1_hit |
| wiper_caution_001 | maintenance_check | safety_notice | 1 | 1 | 1 | dense,bm25,hybrid | dense,bm25,hybrid | 63 | 63 | 63 | N/A | N/A | N/A | all_top1_hit,section_metadata_missing |

## By Category

| group | case_count | evidence_hit@1 | evidence_hit@3 | evidence_hit@5 | mrr | term_coverage_ratio@5 | noise_rate@5 | duplicate_chunk_id_rate@5 | same_page_duplicate_rate@5 | cross_page_repeated_content_rate@5 | final_context_hit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| explanation | 9 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9556 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| forbidden_condition | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| location_query | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| maintenance_check | 12 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| parameter_query | 6 | 0.6667 | 1.0000 | 1.0000 | 0.8056 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| procedure | 27 | 0.7407 | 0.9630 | 1.0000 | 0.8426 | 0.8611 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| usage_guidance | 6 | 0.8333 | 1.0000 | 1.0000 | 0.9167 | 0.7917 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| warning_notice | 18 | 0.7222 | 1.0000 | 1.0000 | 0.8611 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0444 | N/A |

## By Intent Type

| group | case_count | evidence_hit@1 | evidence_hit@3 | evidence_hit@5 | mrr | term_coverage_ratio@5 | noise_rate@5 | duplicate_chunk_id_rate@5 | same_page_duplicate_rate@5 | cross_page_repeated_content_rate@5 | final_context_hit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| broad_usage_guidance | 6 | 0.8333 | 1.0000 | 1.0000 | 0.9167 | 0.7917 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| check_procedure | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| concept_explanation | 9 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9556 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| forbidden_condition | 6 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1333 | N/A |
| limit_parameter | 3 | 0.3333 | 1.0000 | 1.0000 | 0.6111 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| location_and_operation | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| location_and_parameter | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| location_query | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| maintenance_guidance | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| post_event_checklist | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| safety_notice | 18 | 0.7222 | 1.0000 | 1.0000 | 0.8611 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| specific_operation | 21 | 0.6667 | 0.9524 | 1.0000 | 0.7976 | 0.8214 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| state_explanation | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |

## Failure Cases

No failure cases by current coarse criteria.