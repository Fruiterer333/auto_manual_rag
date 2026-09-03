# V4.5.1 Generation Reproducibility 报告

## 1. 动机与范围

V4.4 formal baseline 的 generation request 仅显式发送 `model`、`prompt` 与
`stream=false`。因此当时的运行身份可审计，但 temperature、seed 和其他 runtime
options 依赖 Ollama 默认行为，无法构成严格的重复生成配置。

本阶段只将 generation configuration 显式化、写入 evaluation artifact，并提供重复运行
稳定性验证工具。没有修改 V4.4/V4.5 冻结 artifact、检索、rerank、prompt、context budget、
sanitizer、V4.3 semantics 或 answer-eval contract。

## 2. 修改前的 Generation 行为

- `/api/generate` payload：`model`、`prompt`、`stream=false`。
- temperature：未发送，来源为 Ollama 默认行为。
- seed：未发送，来源为 Ollama 默认行为。
- options：未发送。
- V4.4 historical baseline 保持不变；本报告不重写其 metadata 或结论。

## 3. 集中式 Generation Configuration 设计

单一来源为 `Settings`：

- `OLLAMA_TEMPERATURE=0.0`
- `OLLAMA_SEED=42`

`OllamaClient` 通过统一的 `get_generation_options()` 和
`build_generation_request_payload()` 构造请求；production QA 与 answer evaluation
共用该 client，因此不存在评测脚本单独硬编码 sampling 参数的第二套逻辑。

Ollama 官方 `/api/generate` 文档将 `options` 定义为控制文本生成的 runtime options；
官方 Modelfile 参数文档列出了 `temperature` 与 `seed`，并说明固定 seed 用于同一提示的
重复生成。[Generate API](https://docs.ollama.com/api/generate)
和 [Modelfile 参数参考](https://docs.ollama.com/modelfile)。

## 4. 显式控制与继承参数

### 显式控制

请求体的实际发送值为：

```json
{
  "stream": false,
  "options": {
    "temperature": 0.0,
    "seed": 42
  }
}
```

- `stream`：显式 `false`
- `temperature`：显式 `0.0`，以消除本项目层面的随机采样温度歧义
- `seed`：显式 `42`，用于同一运行环境下的重复运行验证
- timeout：显式 `120` 秒

这不是 parameter tuning：本阶段只固定最小的 sampling identity，不增加 top-p、top-k、
repeat penalty 或上下文长度等新实验变量。

### 仍继承的参数

`top_k`、`top_p`、`min_p`、`repeat_penalty`、`num_predict`、`num_ctx` 未主动控制，
在 artifact 中明确记录为 `ollama_model_or_service_defaults`。这些值不是本项目显式冻结的
参数，不能被误报为固定配置。

## 5. Artifact Metadata 变化

后续 `scripts/evaluate_answers.py` 的 run-level config 会记录：

- `generation_stream` 与来源；
- `generation_temperature`、`generation_seed` 及其 `settings_explicit` 来源；
- 完整的 `generation_options`；
- inherited option 名称及其默认来源；
- timeout 及来源；
- 既有 Ollama version、model tag、model digest runtime metadata。

这只影响未来运行生成的 artifact，不追溯修改 V4.4 baseline。

## 6. Repeated-run Stability Verification 方法

新增 `scripts/verify_generation_reproducibility.py`。默认从冻结 answer-eval dataset
选取四条代表性 case，并在完全相同配置下各运行三次：

1. `abs_explanation_answer_001`：normal factual/explanation；
2. `epb_enable_release_answer_001`：procedure；
3. `overspeed_condition_answer_001`：condition-sensitive；
4. `unsupported_voice_brake_calibration_answer_001`：hard negative。

每次记录 model/runtime metadata、显式与继承 generation options、`prompt_evidence` 的
ID/顺序/chunk identity、raw answer 和 final answer。稳定性同时要求：

- raw answer 完全一致；
- final answer 完全一致；
- prompt Evidence identity/order 完全一致。

不会仅比较 final answer，因为 sanitizer 可能隐藏 raw generation 的差异。

## 7. 当前重复运行结果

最初的 Codex sandbox 无法访问 host Ollama，因而未在该环境内执行 generation。随后已在
可访问本机 Ollama 的环境中实际运行 verification runner。以下结论均来自：

- [stability JSON](/Users/fruiterer/Downloads/auto_manual_rag/reports/evaluation/v4_5_1_generation_stability.json)
- [stability Markdown](/Users/fruiterer/Downloads/auto_manual_rag/reports/evaluation/v4_5_1_generation_stability.md)

实际 artifact 记录：

- `verification_status = VERIFIED`
- 4 条 representative case，每条运行 3 次；共 12 次 generation。
- 4/4 case 的 `prompt_evidence_identity_exact_match = true`。
- 4/4 case 的 `raw_answer_exact_match = true`。
- 4/4 case 的 `final_answer_exact_match = true`。
- 4/4 case 的 `case_stable = true`。
- runtime identity：`qwen2.5:7b`、Ollama `0.33.2`、model digest
  `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`。
- generation configuration：`stream=false`、`temperature=0.0`、`seed=42`；
  与本报告第 4 节一致。

因此，stability JSON、stability Markdown 与本主报告对本机验证状态没有冲突。

如需在新的 runtime、模型 digest 或 generation configuration 下复核，应重新执行：

```bash
.venv/bin/python scripts/verify_generation_reproducibility.py
```

本次 `REPEATED_RUN_STABILITY_VERIFIED=YES` 的结论仅限于当前测试环境、当前 Ollama
版本、当前模型 digest、当前 generation configuration 和当前 inference backend 下的
exact-output stability；不代表跨硬件、跨 Ollama 版本、跨 inference backend 或跨模型构建的
普适确定性。

## 8. Reproducibility Assessment

- `GENERATION_PARAMETERS_EXPLICIT = YES`
- `REPEATED_RUN_STABILITY_VERIFIED = YES`
- `STRICT_REPRODUCIBILITY_READY = YES`
- `READY_FOR_V4_6_CONTROLLED_EXPERIMENTS = YES`

这里的 `STRICT_REPRODUCIBILITY_READY=YES` 表示：在已记录的当前测试环境中，固定 runtime
identity 与 generation configuration 后，重复运行的 raw/final output 和 prompt Evidence
identity/order 已通过 exact-match 验证。它不是对跨环境 bit-for-bit determinism 的宣称。

## 9. 已知限制

- 固定 temperature/seed 不能单独保证跨环境 bit-for-bit deterministic。
- 未显式控制的 options 仍受模型或服务默认值影响，并已如实记录。
- 本轮不比较 answer quality，不重跑 V4.4 12-case formal baseline。
- elapsed 不是正式 online latency 指标。
