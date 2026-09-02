# V4.3.1 Formal Answer Baseline Generation Reproducibility Preflight

## Key Findings

当前 Ollama generation 请求只显式发送以下 payload：

```json
{
  "model": "qwen2.5:7b",
  "prompt": "<constructed prompt>",
  "stream": false
}
```

客户端显式使用 `timeout=120` 秒。它不发送 `temperature`、`seed` 或 `options`，因此这些 generation controls 不是被冻结的显式值，而是 Ollama/model 的未设置默认行为。V4.3.1 不改变 payload，也不设置新的 temperature 或 seed。

本次只读运行时 metadata lookup 请求了 `/api/version` 与 `/api/tags`，没有调用 `/api/generate`。当前本机 `http://127.0.0.1:11434` 不可连接，因此 Ollama version 和 model digest 的 preflight 值为 `unknown`。正式 baseline runner 已改为在每次运行前 best-effort 采集这两个字段；采集失败会保留 `unknown` 并记录原因，不会改变或阻断 generation behavior。

## Evaluation Semantics Freeze vs Generation Configuration Freeze

Evaluation semantics 已在 V4.3 冻结：dataset contract、deterministic term normalization、human review rubric、Evidence snapshot、raw/final answer capture 均不在本次变更范围内。

Generation configuration freeze 的含义不同：artifact 必须准确记录实际发送给 Ollama 的显式参数，以及未设置但会依赖服务默认值的参数。它不要求本次为了“更严格”而改变 production generation behavior。

## Run-Level Metadata Preflight

| Field | Current Value | Explicit / Default / Unknown | Recorded in Artifact? | Action |
| --- | --- | --- | --- | --- |
| `answer_eval_semantics_version` | `v4.3` | Explicit | Yes | Keep frozen. |
| `answer_eval_dataset_sha256` | Dataset SHA-256 at run time | Explicitly computed | Yes | Require it to match the intended frozen dataset before comparing runs. |
| `llm_model` / model tag | `qwen2.5:7b` | Explicit Settings value | Yes | Keep current tag; do not change behavior. |
| `ollama_model_digest` | `unknown` in this preflight | Unknown; `/api/tags` unavailable locally | Yes, best effort | Start Ollama before the formal run so the runner can record a digest if the service exposes one. |
| `ollama_version` | `unknown` in this preflight | Unknown; `/api/version` unavailable locally | Yes, best effort | Start Ollama before the formal run so the runner can record the service version. |
| `generation_stream` | `false` | Explicit | Yes | Keep frozen. |
| `generation_temperature` | `null` | Default / unset | Yes | Do not set in this task; document that Ollama/model default behavior applies. |
| `generation_seed` | `null` | Default / unset | Yes | Do not set in this task; document that Ollama/model default behavior applies. |
| `generation_options` | `null` | Not sent | Yes | Keep absent unless a separately approved generation-config change is made. |
| `generation_timeout_seconds` | `120` | Explicit | Yes | Keep current timeout. |
| `retrieval_mode` | `hybrid` | Settings / CLI resolved value | Yes | Freeze per artifact. |
| `rerank_enabled` | `false` | Explicit Settings value | Yes | Formal baseline should use the current production default. |
| `top_k` | `5` | Explicit CLI default | Yes | Freeze per artifact. |
| `metadata_context_selection_enabled` | `true` | Explicit Settings value | Yes | Freeze per artifact. |
| `neighbor_expansion_enabled` | `false` | Explicit Settings value | Yes | Keep disabled. |
| `max_contexts` | `5` when `top_k=5` | Derived deterministically from final context limit | Yes | Freeze per artifact. |
| `max_context_chars` | `6000` | Explicit Settings value | Yes | Freeze per artifact. |

`ollama_model_digest` is a snapshot of the locally installed model exposed by Ollama, not an instruction to pull, replace or pin a model. If `/api/tags` does not expose a digest, the artifact must retain `null`/`unknown` rather than inventing an identifier.

## What a Formal Baseline Can Reproduce

The formal artifact can now reconstruct the evaluation semantics, dataset identity, retrieval/rerank/context configuration, exact prompt Evidence snapshot, raw/final answers, explicitly sent generation payload controls, timeout, and best-effort Ollama runtime identity.

It cannot strictly guarantee byte-identical generation across machines or time while temperature and seed remain unset and service version/model digest are unavailable or differ. Ollama defaults, installed model content, service version and hardware may still affect output.

## Readiness Decision

| Decision | Result | Reason |
| --- | --- | --- |
| `SEMANTICS_READY_FOR_BASELINE` | `YES` | V4.3 semantics are frozen and validation has no outstanding contract review. |
| `GENERATION_AUDITABILITY_READY` | `YES` | The artifact records explicit controls, unset/default controls, timeout, runtime version/digest when available, and `unknown` when not available. |
| `STRICT_REPRODUCIBILITY_READY` | `NO` | temperature and seed are intentionally unset; this preflight could not obtain Ollama version or model digest; model/service defaults remain environment-dependent. |

It is safe to proceed with the first formal baseline as an auditable baseline, provided Ollama is started first and `scripts/validate_answer_eval_set.py` passes immediately before the run. This does not make the run a strict cross-machine deterministic experiment.

## Required Next-Run Procedure

1. Start the same intended Ollama service and verify the target model is available.
2. Run `python scripts/validate_answer_eval_set.py` to confirm provenance and V4.3 semantics validation.
3. Run the formal baseline with the frozen production defaults: hybrid retrieval, rerank disabled, `top_k=5`, metadata context selection enabled, neighbor expansion disabled, `max_contexts=5`, `max_context_chars=6000`, model tag `qwen2.5:7b`, and `stream=false`.
4. Preserve the generated Markdown and JSON pair. Verify the artifact contains dataset SHA-256, `ollama_version`, `ollama_model_digest`, and the generation metadata fields. Unknown runtime fields must remain visible rather than being filled by assumption.

## No Behavior Change

V4.3.1 does not modify retrieval, rerank, prompt wording, evaluator semantics, answer contracts, parser, splitter, context selection, neighbor expansion, or LLM generation payload. No answer generation, Answer Evaluation run, retrieval evaluation, index rebuild, staging, or commit occurred during this preflight.
