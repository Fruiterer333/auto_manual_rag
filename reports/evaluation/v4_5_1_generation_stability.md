# V4.5.1 重复生成稳定性验证

- 验证状态：`VERIFIED`
- V4.3 语义版本：`v4.3`
- 每条 case 运行次数：3
- case 数量：4

## Generation Configuration

- generation_stream: `false`
- generation_stream_source: `"explicit"`
- generation_temperature: `0.0`
- generation_temperature_source: `"settings_explicit"`
- generation_seed: `42`
- generation_seed_source: `"settings_explicit"`
- generation_options: `{"temperature": 0.0, "seed": 42}`
- generation_options_source: `"settings_explicit"`
- generation_inherited_options: `["top_k", "top_p", "min_p", "repeat_penalty", "num_predict", "num_ctx"]`
- generation_inherited_options_source: `"ollama_model_or_service_defaults"`
- generation_timeout_seconds: `120`
- generation_timeout_source: `"explicit"`

## Ollama Runtime

- ollama_base_url: `"http://127.0.0.1:11434"`
- ollama_version: `"0.33.2"`
- ollama_version_source: `"api_version"`
- ollama_model_tag: `"qwen2.5:7b"`
- ollama_model_digest: `"845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"`
- ollama_model_digest_source: `"api_tags"`
- ollama_runtime_metadata_error: `null`

## Case 结果

| case_id | raw exact | final exact | Evidence identity exact | stable |
| --- | --- | --- | --- | --- |
| `abs_explanation_answer_001` | True | True | True | True |
| `epb_enable_release_answer_001` | True | True | True | True |
| `overspeed_condition_answer_001` | True | True | True | True |
| `unsupported_voice_brake_calibration_answer_001` | True | True | True | True |

## 判定

- REPEATED_RUN_STABILITY_VERIFIED = YES
- 完全相同的 raw/final output 仅能说明当前本机、当前 Ollama 版本、当前模型 digest 和当前后端下的重复运行稳定性，不代表跨机器或跨版本的普适确定性。
