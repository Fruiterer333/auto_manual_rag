# V4.3 Answer Evaluation Semantics Freeze

## Evaluation Philosophy

V4.3 冻结 Answer Evaluation 的判定语义，不优化模型回答，也不修改 production RAG。自动检查只覆盖可以稳定复现的字符串与结构条件；groundedness、correctness、completeness、condition handling 和 safety preservation 仍由人工依据模型实际看到的 `prompt_evidence` 审查。

自动指标不能替代人工语义判断。`citation.quote` 仅用于用户引用展示，不是 groundedness 的审查依据。`must_include_points` 是人工 review guidance，当前不做自动 normalization 或句子级自动评分。

## Deterministic Normalization

当前 Answer Evaluation semantics version 为 `v4.3`。`must_include_terms` 和 `must_not_include_terms` 的比较采用同一套保守、确定性 normalization：

1. Unicode NFKC，统一全角和半角字符；
2. 英文使用 case-insensitive comparison；
3. 删除不影响词项语义的常见中英文标点；
4. 删除多余空白；
5. 将数字与厘米单位的格式统一为 `<number>cm`，因此 `10 cm`、`10cm`、`10 厘米` 和 `10厘米` 等价。

评测 artifact 继续保存 dataset 中的原始 term。`matched_must_include_terms`、`missing_must_include_terms` 和 `forbidden_term_hits` 均返回原始值，normalization 只用于 comparison。

## Normalization Boundaries

Normalization 不处理语义近似，不包含 embedding similarity、编辑距离、同义词扩展、stemming、LLM judge 或单位数值换算。

以下内容不会被错误视为等价：

- `10 cm` 与 `30 cm`；
- `10 cm` 与 `10 m`；
- `立即停车` 与 `停车灯`，也不会把只有“停车”的答案自动视为覆盖“立即停车”；
- `ABS故障` 与 `ABS正常`；
- `踩下制动踏板` 与 `松开制动踏板`。

安全关键条件继续使用严格 substring semantics。该 normalization 只减少明确的格式差异 false negative，不尝试判断句子级语义。

## Human Review Rubric

所有 0/1/2 分项允许 `null`，用于表示尚未完成正式人工审查。两个布尔项也允许 `null`。人工判断必须以本次运行保存的精确 `prompt_evidence`、`raw_answer` 和 `final_answer` 为依据。

### Groundedness

- `2` Fully Grounded：核心事实和操作说明均由实际 `prompt_evidence` 支持，不存在实质性 unsupported claim。
- `1` Partially Grounded：主要结论有依据，但包含次要的无依据延伸、不必要解释或轻微超出 Evidence 的内容，且不改变主要操作或安全含义。
- `0` Not Grounded：关键事实、操作步骤、条件或安全结论无法由 `prompt_evidence` 支持，或明显由模型自行补充。

### Correctness

- `2` Correct：核心事实、方向、条件、步骤和状态均正确。
- `1` Partially Correct：主体正确，但存在不改变主要操作结果的非关键细节错误或模糊表达。
- `0` Incorrect：存在关键事实错误，例如启用/释放反转、普通/紧急操作混淆、条件关系错误、状态解释错误或会导致错误结果的操作顺序。

### Completeness

- `2` Complete：覆盖回答问题所需的全部核心事实。
- `1` Partially Complete：主要答案存在，但遗漏一个或多个非安全、非关键点。
- `0` Incomplete：遗漏使答案无法正确执行，或遗漏关键步骤、事实或条件。

### Condition Handling

- `2` Conditions Preserved：正确保留全部关键前提、车辆状态和适用条件。
- `1` Minor Condition Loss：存在轻微条件遗漏，但不会使用户在错误场景下执行操作。
- `0` Condition Failure：遗漏、混淆或错误扩展关键条件，例如混用普通/紧急操作、点火状态、P 挡、制动踏板或 AUTO/manual 模式条件。

### Safety Preservation

- `2` Safety Preserved：保留全部关键 warning、caution 和 required safety action。
- `1` Minor Safety Degradation：安全主旨正确，但遗漏非关键 warning 细节。
- `0` Safety Failure：遗漏或错误表达关键安全动作、禁止条件或警告。

### Unsupported Claim

当 `final_answer` 包含 `prompt_evidence` 无法支持的实质性事实陈述时为 `true`。语言组织、连接词或不增加事实含义的改写不构成 unsupported claim。

### Critical Safety Omission

当 `final_answer` 遗漏 answer contract 或 manual truth 明确要求的关键安全动作、禁止条件或警告时为 `true`。

## Cross-Metric Consistency

人工 review 应遵守以下一致性约束，但本版本不实现自动约束引擎：

1. `critical_safety_omission=true` 时，Safety Preservation 不得为 `2`，通常应为 `0`；
2. 核心操作方向错误时，Correctness 必须为 `0`；
3. 关键条件被混淆时，Condition Handling 必须为 `0`；
4. 回答的主要事实来自 unsupported hallucination 时，Groundedness 必须为 `0`。

## Hard Negative Scoring

`unsupported_voice_brake_calibration_answer_001` 是 hard negative。它没有正向 Evidence，但若回答明确表示手册中没有可靠依据，并且没有编造语音校准步骤，则 Groundedness、Correctness 和 Completeness 均可评为 `2`。Completeness 在此衡量是否完整执行 insufficient-evidence contract，而不是是否生成正向操作步骤。

## Remote Start Contract Review

### Current Contract Before V4.3

问题为“哪些情况下无法远程启动发动机？”。旧 contract 只要求覆盖四组条件：挡位不在驻车挡、网络信号丢失、机舱盖或车门未锁定、发动机故障或维修模式。它没有完整覆盖 canonical Evidence 中的冷却液液位较低、燃油油位较低和车内有遥控钥匙。

### Manual-Supported Facts

当前 V3.5 canonical Evidence 明确列出八类阻断条件：

1. 挡位不在驻车挡（P）；
2. 冷却液液位较低；
3. 燃油油位较低；
4. 车内有遥控钥匙；
5. 网络信号丢失；
6. 发动机机舱盖或车门未锁定；
7. 发动机出现故障；
8. 车辆设置为维修模式。

### Question Scope

“哪些情况下”是开放式列举问题。该问题没有限定只询问其中几类条件，因此 answer contract 应覆盖 canonical Evidence 明确列出的全部阻断条件，而不是挑选部分条件。

### Final Contract After V4.3

`remote_start_blocked_answer_001` 的 `must_include_terms` 已补充为可检查全部八类条件的词项；`must_include_points` 调整为八个核心覆盖点。Evidence、问题、source case 和禁止性约束保持不变，`ANSWER_CONTRACT_REVIEW` 标记已关闭。

### Rationale

本次修改依据 question wording、manual truth 和当前 V3.5 canonical Evidence，不依据历史模型回答。它修正的是原 contract 的不完整，而不是为了提高或降低某次模型评测结果。

## Evaluation Semantics Version

- `answer_eval_semantics_version`: `v4.3`
- dataset case count: `12`
- positive cases: `11`
- hard negative cases: `1`
- dataset SHA-256 at freeze time: `c3b06add0f3a906597a652997f824cd3c3cccc2e30eda684d6a98761ba493f8a`

任何影响 normalization、rubric 或 answer contract 语义的后续修改都必须提升 semantics version。不同 semantics version 的 baseline 不应直接解释为模型或 production RAG 的效果变化。

## Formal Baseline Artifact Naming

正式运行默认使用：

```text
reports/evaluation/v4_answer_baseline_<retrieval_mode>_<rerank|no_rerank>_<YYYYMMDD_HHMMSS>.md
reports/evaluation/v4_answer_baseline_<retrieval_mode>_<rerank|no_rerank>_<YYYYMMDD_HHMMSS>.json
```

该命名与旧的 `answer_eval_v1` diagnostic artifact 明确区分。正式 artifact 必须保留同名 Markdown 与 JSON，JSON 用于机器读取，Markdown 用于人工 review。

## Freeze State

正式 baseline artifact 当前记录：

- answer eval dataset 路径与 SHA-256；
- case count；
- answer evaluation semantics version；
- LLM model；
- embedding model；
- retrieval mode；
- rerank enabled、model、top-n 和 output top-k；
- query top-k；
- metadata context selection 状态；
- neighbor expansion 状态；
- prompt max contexts 和 max context chars；
- generation stream 状态；
- 每条 case 的精确 `prompt_evidence`、`raw_answer`、`final_answer` 和 citations。

Formal baseline 的前置 gate 是先运行 `scripts/validate_answer_eval_set.py`，确认 provenance 和 semantics validation 均通过。runner 自身会 fail-fast 检查 semantics version、rubric schema 和 outstanding contract review。

当前冻结状态：

- provenance valid；
- sanitizer 与 leak detector 已修复；
- exact model-visible Evidence snapshot 可用；
- raw/final answer 可审计；
- deterministic normalization 已冻结；
- human rubric 已冻结；
- outstanding contract review 为 0；
- semantics version 已冻结为 `v4.3`。

`READY_FOR_FORMAL_V4_BASELINE = YES`

建议下一次正式 baseline 固定使用当前 production 默认：`retrieval_mode=hybrid`、`rerank_enabled=false`、`top_k=5`、metadata context selection enabled、neighbor expansion disabled、`max_contexts=5`、`max_context_chars=6000`、`llm_model=qwen2.5:7b`、`generation_stream=false`、semantics version `v4.3`，并在运行前确认 dataset SHA-256 与冻结值一致。

## Remaining Risks

1. deterministic term coverage 仍是 substring-based proxy，不能替代句子级语义审查；
2. `must_include_points`、`must_not_claim` 和 `critical_warning_points` 仍需人工判断；
3. Ollama 请求未显式设置 temperature、seed 等 sampling options，当前 artifact 只能准确记录实际 payload 使用 model、prompt 和 `stream=false`，模型服务默认参数与 Ollama 版本仍可能影响跨环境复现；
4. model digest、Ollama 版本和宿主硬件尚未进入 artifact metadata；
5. 当前 12 条数据是 dev evaluation set，不是最终 test benchmark；
6. 本轮未调用 Ollama、未运行正式 Answer Evaluation，也未修改 prompt、retrieval、rerank、parser、splitter、context selection 或 generation behavior。
