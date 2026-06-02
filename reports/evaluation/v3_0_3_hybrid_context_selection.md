# Retrieval Evaluation Report

- generated_at: 2026-06-01T22:19:14
- dataset: `data/eval/manual_eval_set.jsonl`
- case_count: 29
- retrieval_modes: hybrid
- top_k: 5
- use_context_selection: True
- elapsed_seconds: 14.44

## Overall Metrics

| metric | value |
| --- | ---: |
| acceptable_section_hit@1 | 0.4483 |
| acceptable_section_hit@3 | 0.6897 |
| acceptable_section_hit@5 | 0.6897 |
| all_terms_hit@1 | 0.5862 |
| all_terms_hit@3 | 0.7931 |
| all_terms_hit@5 | 0.8966 |
| any_term_hit@1 | 0.8621 |
| any_term_hit@3 | 1.0000 |
| any_term_hit@5 | 1.0000 |
| average_first_hit_rank | 1.2414 |
| case_count | 29 |
| content_type_hit@1 | 0.8966 |
| content_type_hit@3 | 0.9655 |
| content_type_hit@5 | 1.0000 |
| cross_page_repeated_content_rate@1 | 0.0000 |
| cross_page_repeated_content_rate@3 | 0.0000 |
| cross_page_repeated_content_rate@5 | 0.0138 |
| duplicate_chunk_id_rate@1 | 0.0000 |
| duplicate_chunk_id_rate@3 | 0.0000 |
| duplicate_chunk_id_rate@5 | 0.0000 |
| evidence_hit@1 | 0.7931 |
| evidence_hit@3 | 1.0000 |
| evidence_hit@5 | 1.0000 |
| expected_section_hit@1 | 0.4483 |
| expected_section_hit@3 | 0.6897 |
| expected_section_hit@5 | 0.6897 |
| final_context_count | 5.0000 |
| final_context_hit | 1.0000 |
| first_evidence_hit_rank | 1.2414 |
| mrr | 0.8908 |
| noise_rate@1 | 0.0000 |
| noise_rate@3 | 0.0000 |
| noise_rate@5 | 0.0000 |
| page_hit@1 | 0.7931 |
| page_hit@3 | 0.9655 |
| page_hit@5 | 1.0000 |
| retrieved_count | 5.0000 |
| same_page_duplicate_rate@1 | 0.0000 |
| same_page_duplicate_rate@3 | 0.0000 |
| same_page_duplicate_rate@5 | 0.0000 |
| term_coverage_ratio@1 | 0.6655 |
| term_coverage_ratio@3 | 0.8626 |
| term_coverage_ratio@5 | 0.9534 |

## By Retrieval Mode

| retrieval_mode | case_count | evidence_hit@1 | evidence_hit@3 | evidence_hit@5 | mrr | average_first_hit_rank | expected_section_hit@5 | acceptable_section_hit@5 | any_term_hit@5 | all_terms_hit@5 | term_coverage_ratio@5 | noise_rate@5 | duplicate_chunk_id_rate@5 | same_page_duplicate_rate@5 | cross_page_repeated_content_rate@5 | final_context_hit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hybrid | 29 | 0.7931 | 1.0000 | 1.0000 | 0.8908 | 1.2414 | 0.6897 | 0.6897 | 1.0000 | 0.8966 | 0.9534 | 0.0000 | 0.0000 | 0.0000 | 0.0138 | 1.0000 |

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
| warning_notice | 6 | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0667 | 1.0000 |

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
| safety_notice | 6 | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| specific_operation | 7 | 0.5714 | 1.0000 | 1.0000 | 0.7619 | 0.8429 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| state_explanation | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## Failure Cases

No failure cases by current coarse criteria.