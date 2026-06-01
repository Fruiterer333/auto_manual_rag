# Retrieval Evaluation Report

- generated_at: 2026-05-31T17:25:09
- dataset: `data/eval/manual_eval_set.jsonl`
- case_count: 30
- retrieval_modes: hybrid
- top_k: 5
- use_context_selection: True
- elapsed_seconds: 13.19

## Overall Metrics

| metric | value |
| --- | ---: |
| acceptable_section_hit@1 | 0.4333 |
| acceptable_section_hit@3 | 0.6667 |
| acceptable_section_hit@5 | 0.6667 |
| all_terms_hit@1 | 0.5667 |
| all_terms_hit@3 | 0.7667 |
| all_terms_hit@5 | 0.8667 |
| any_term_hit@1 | 0.8667 |
| any_term_hit@3 | 1.0000 |
| any_term_hit@5 | 1.0000 |
| average_first_hit_rank | 1.2414 |
| case_count | 30 |
| content_type_hit@1 | 0.8667 |
| content_type_hit@3 | 0.9333 |
| content_type_hit@5 | 0.9667 |
| cross_page_repeated_content_rate@1 | 0.0000 |
| cross_page_repeated_content_rate@3 | 0.0000 |
| cross_page_repeated_content_rate@5 | 0.0133 |
| duplicate_chunk_id_rate@1 | 0.0000 |
| duplicate_chunk_id_rate@3 | 0.0000 |
| duplicate_chunk_id_rate@5 | 0.0000 |
| evidence_hit@1 | 0.7667 |
| evidence_hit@3 | 0.9667 |
| evidence_hit@5 | 0.9667 |
| expected_section_hit@1 | 0.4333 |
| expected_section_hit@3 | 0.6667 |
| expected_section_hit@5 | 0.6667 |
| final_context_count | 5.0000 |
| final_context_hit | 0.9667 |
| first_evidence_hit_rank | 1.2414 |
| mrr | 0.8611 |
| noise_rate@1 | 0.0000 |
| noise_rate@3 | 0.0000 |
| noise_rate@5 | 0.0000 |
| page_hit@1 | 0.7667 |
| page_hit@3 | 0.9333 |
| page_hit@5 | 0.9667 |
| retrieved_count | 5.0000 |
| same_page_duplicate_rate@1 | 0.0000 |
| same_page_duplicate_rate@3 | 0.0000 |
| same_page_duplicate_rate@5 | 0.0000 |
| term_coverage_ratio@1 | 0.6500 |
| term_coverage_ratio@3 | 0.8406 |
| term_coverage_ratio@5 | 0.9283 |

## By Category

| group | case_count | evidence_hit@1 | evidence_hit@3 | evidence_hit@5 | mrr | term_coverage_ratio@5 | noise_rate@5 | duplicate_chunk_id_rate@5 | same_page_duplicate_rate@5 | cross_page_repeated_content_rate@5 | final_context_hit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| explanation | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| forbidden_condition | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| location_query | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| maintenance_check | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| parameter_query | 2 | 0.5000 | 1.0000 | 1.0000 | 0.7500 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| procedure | 9 | 0.6667 | 1.0000 | 1.0000 | 0.8148 | 0.8778 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| usage_guidance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| warning_notice | 7 | 0.5714 | 0.8571 | 0.8571 | 0.7143 | 0.8857 | 0.0000 | 0.0000 | 0.0000 | 0.0571 | 0.8571 |

## By Intent Type

| group | case_count | evidence_hit@1 | evidence_hit@3 | evidence_hit@5 | mrr | term_coverage_ratio@5 | noise_rate@5 | duplicate_chunk_id_rate@5 | same_page_duplicate_rate@5 | cross_page_repeated_content_rate@5 | final_context_hit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| alarm_handling | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| broad_usage_guidance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| check_procedure | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| concept_explanation | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| forbidden_condition | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.2000 | 1.0000 |
| limit_parameter | 1 | 0.0000 | 1.0000 | 1.0000 | 0.5000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| location_and_operation | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| location_and_parameter | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| location_query | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| maintenance_guidance | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| post_event_checklist | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| post_event_warning | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| safety_notice | 6 | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| specific_operation | 7 | 0.5714 | 1.0000 | 1.0000 | 0.7619 | 0.8429 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| state_explanation | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## Failure Cases

- `seatbelt_after_collision_warning_001` mode=hybrid reasons=no_evidence_hit question=车辆发生碰撞后，安全带相关部件有什么需要注意的风险？