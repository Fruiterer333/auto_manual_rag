# V4.7 选定 Answer Model 重复运行稳定性验证

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
- generation_think: `false`
- generation_think_source: `"settings_explicit"`
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
- ollama_model_tag: `"qwen3.5:9b"`
- ollama_model_digest: `"6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"`
- ollama_model_digest_source: `"api_tags"`
- ollama_runtime_metadata_error: `null`

## Case 结果

| case_id | raw exact | final exact | Evidence identity/order/text exact | stable |
| --- | --- | --- | --- | --- |
| `epb_poweroff_release_answer_001` | True | True | True | True |
| `remote_key_start_answer_001` | True | True | True | True |
| `pressure_wash_warning_answer_001` | True | True | True | True |
| `unsupported_voice_brake_calibration_answer_001` | True | True | True | True |

## 判定

- REPEATED_RUN_STABILITY_VERIFIED = YES
- 完全相同的 raw/final output 仅能说明当前本机、当前 Ollama 版本、当前模型 digest 和当前后端下的重复运行稳定性，不代表跨机器或跨版本的普适确定性。
