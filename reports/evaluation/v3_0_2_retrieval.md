# Retrieval Evaluation Report

- generated_at: 2026-05-30T23:38:49
- dataset: `data/eval/manual_eval_set.jsonl`
- case_count: 30
- retrieval_modes: dense, bm25, hybrid
- top_k: 5
- use_context_selection: False
- elapsed_seconds: 16.34

## Overall Metrics

| metric | value |
| --- | ---: |
| acceptable_section_hit@1 | 0.4556 |
| acceptable_section_hit@3 | 0.6222 |
| acceptable_section_hit@5 | 0.6667 |
| all_terms_hit@1 | 0.5778 |
| all_terms_hit@3 | 0.7556 |
| all_terms_hit@5 | 0.8333 |
| any_term_hit@1 | 0.8778 |
| any_term_hit@3 | 1.0000 |
| any_term_hit@5 | 1.0000 |
| average_first_hit_rank | 1.2414 |
| case_count | 90 |
| content_type_hit@1 | 0.8333 |
| content_type_hit@3 | 0.9333 |
| content_type_hit@5 | 0.9556 |
| cross_page_repeated_content_rate@1 | 0.0000 |
| cross_page_repeated_content_rate@3 | 0.0000 |
| cross_page_repeated_content_rate@5 | 0.0089 |
| duplicate_chunk_id_rate@1 | 0.0000 |
| duplicate_chunk_id_rate@3 | 0.0000 |
| duplicate_chunk_id_rate@5 | 0.0000 |
| evidence_hit@1 | 0.8000 |
| evidence_hit@3 | 0.9556 |
| evidence_hit@5 | 0.9667 |
| expected_section_hit@1 | 0.4444 |
| expected_section_hit@3 | 0.6111 |
| expected_section_hit@5 | 0.6556 |
| first_evidence_hit_rank | 1.2414 |
| mrr | 0.8731 |
| noise_rate@1 | 0.0000 |
| noise_rate@3 | 0.0000 |
| noise_rate@5 | 0.0000 |
| page_hit@1 | 0.7667 |
| page_hit@3 | 0.9222 |
| page_hit@5 | 0.9556 |
| retrieved_count | 4.9556 |
| same_page_duplicate_rate@1 | 0.0000 |
| same_page_duplicate_rate@3 | 0.0000 |
| same_page_duplicate_rate@5 | 0.0000 |
| term_coverage_ratio@1 | 0.6850 |
| term_coverage_ratio@3 | 0.8494 |
| term_coverage_ratio@5 | 0.9133 |

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
| warning_notice | 21 | 0.6190 | 0.8571 | 0.8571 | 0.7381 | 0.8857 | 0.0000 | 0.0000 | 0.0000 | 0.0381 | N/A |

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
| post_event_warning | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| safety_notice | 18 | 0.7222 | 1.0000 | 1.0000 | 0.8611 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| specific_operation | 21 | 0.6667 | 0.9524 | 1.0000 | 0.7976 | 0.8214 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |
| state_explanation | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | N/A |

## Failure Cases

- `seatbelt_after_collision_warning_001` mode=dense reasons=no_evidence_hit question=车辆发生碰撞后，安全带相关部件有什么需要注意的风险？
- `seatbelt_after_collision_warning_001` mode=bm25 reasons=no_evidence_hit question=车辆发生碰撞后，安全带相关部件有什么需要注意的风险？
- `seatbelt_after_collision_warning_001` mode=hybrid reasons=no_evidence_hit question=车辆发生碰撞后，安全带相关部件有什么需要注意的风险？