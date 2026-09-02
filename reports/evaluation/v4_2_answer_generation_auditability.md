# V4.2 Answer Generation Auditability

## 问题

V4.1 之前的 Answer Evaluation artifact 只保存最终 answer 和 citations。citation quote 是面向用户的相关短摘录，通常短于 prompt Evidence，也不记录 Evidence ID、顺序、heading path 或截断状态。因此，仅凭 citation quote 无法准确判断模型生成某个 claim 时实际看到了什么，也无法区分模型原始输出与 sanitizer 的修改。

## Evidence Flow

当前 answer generation 链路为：

```text
retrieval candidates
  -> filter / dedup / optional rerank
  -> metadata context selection
  -> optional neighbor expansion
  -> final filter / dedup
  -> final answer context count/char budget
  -> prompt Evidence assembly and serialization
  -> LLM raw answer
  -> internal Evidence sanitizer
  -> final answer + citations
```

Evidence ID 分配、Evidence body 截断、`[TRUNCATED]` 标记和最终 prompt serialization 均发生在 `app/rag/prompts/answer_prompt.py`。

## Snapshot Source of Truth

新增 `assemble_answer_prompt()`，一次生成：

- 最终 prompt string；
- 与该 prompt 同源的 `PromptEvidenceSnapshot` tuple。

每个 snapshot 先生成，再由同一个 snapshot 序列化 Evidence block。artifact 不从完整 `Chunk.text`、final context dump 或 citation quote 反推 model-visible text，从而避免 prompt serialization 后续变化导致审计数据漂移。

原有 `build_answer_prompt()` 保持原签名和返回类型，内部委托给 `assemble_answer_prompt()` 并只返回 prompt，保证已有调用方兼容。

## Snapshot Schema

每条 prompt Evidence snapshot 包含：

- `evidence_id`：`E1`、`E2`……；
- `order`：从 1 开始的 prompt 顺序；
- `chunk_id`；
- `page`；
- `chapter`；
- `section`；
- `subsection`；
- `heading_path`：与 prompt 一致的稳定字符串；
- `content_type`；
- `text`：真正序列化进 prompt 的 Evidence body；
- `truncated`；
- `original_text_chars`；
- `prompt_text_chars`。

`subsection` 缺失时 snapshot 保留 `null`，prompt 仍按原格式显示 `N/A`。`heading_path` 使用 `chapter > section > subsection` 形式，不保存 Python list 字面量。

## Truncation Semantics

预算行为保持现有 production semantics：

1. Evidence 在预算内：完整加入，`truncated=false`，snapshot text 与 prompt body 完全一致；
2. 第一条 Evidence 本身超过预算：保留其前缀并追加 `[TRUNCATED]`，`truncated=true`，snapshot 保存实际发送文本，且 `original_text_chars > prompt_text_chars`；
3. 后续 Evidence 加入后会超过剩余预算：停止处理，不重新排序，也不越过该 Evidence 选择更后的内容；未进入 prompt 的 chunk 不出现在 snapshot 中。

QAChain 会将 citation lineage 限制到 prompt assembly 实际保留的 Evidence 数量，确保 artifact 不会出现模型未见过的额外 citation chunk。

## Raw vs Final Answer

新增向后兼容的 `QAChain.answer_with_trace()`：

- `raw_answer`：LLM 返回后、sanitizer 处理前的原始字符串；
- `final_answer`：sanitizer 处理后、实际返回用户的答案；
- `response.answer`：继续等于 `final_answer`；
- `prompt_evidence`：本次 generation 的 exact model-visible snapshots。

普通 `QAChain.answer()` 仍返回原有 `QueryResponse`，API、CLI 和前端不需要知道 trace。

如果没有最终上下文，QAChain 不调用 LLM：`raw_answer=null`、`prompt_evidence=[]`，`final_answer` 使用现有不足证据回答。

## Citation vs Prompt Evidence

两者用途不同：

- `prompt_evidence` 用于 groundedness、unsupported claim 和 sanitizer 审计，保存模型实际看到的正文；
- `citations` 用于最终用户引用展示，quote 可以是较短的 question-relevant excerpt。

它们通过相同 final context lineage 的 `chunk_id` 和顺序关联，但不要求 `citation.quote == prompt_evidence.text`。

## Answer Evaluation Artifact

`AnswerCaseResult` 现保存：

- `case_id`、`question`、`source_case_id`、`answer_type`；
- `raw_answer`、`final_answer`；
- `retrieval_mode`；
- `prompt_evidence`；
- `citations`；
- deterministic checks；
- human review placeholders；
- elapsed time。

generation configuration 继续保存在 run-level `config` 中，包括 model、retrieval mode、rerank 设置、top-k 和 context budget。未保存完整 prompt，以避免 artifact 过大和与模板不必要耦合。

## Backward Compatibility

- production `QueryResponse` schema 和字段语义未改变；
- `QAChain.answer()` 行为和返回类型未改变；
- prompt 文案、Evidence 格式、预算值和截断规则未改变；
- retrieval、rerank、parser、chunker、context selection 算法未改变；
- Answer Eval dataset semantic contract 未改变。

本轮只新增可选 trace 路径，并让 `scripts/evaluate_answers.py` 使用该路径写入可审计 artifact。

## Tests

测试覆盖：

- 无截断 snapshot 的 exact text 和完整 metadata；
- 第一条 Evidence 超预算时的 exact prefix、marker 和字符计数；
- 后续 Evidence 超预算时停止、保持顺序且不进入 snapshot；
- Evidence ID、order、chunk ID 与 prompt 一致；
- raw answer 精确保留、final answer 正确清洗；
- citation quote 可短于 prompt Evidence；
- citation 与 prompt Evidence 的 chunk identity 对齐；
- 无 Evidence 时不调用 LLM，trace 仍合法；
- normal `answer()` 路径向后兼容；
- Answer Evaluation JSON 包含并可重载 raw/final answer 与 prompt snapshots；
- runner 使用 fake QAChain，不调用真实 Ollama。

## Remaining Formal Baseline Blockers

V4.2 已提供人工 groundedness 审计所需的精确 Evidence 与 raw/final answer 边界。正式 baseline 前仍需：

1. deterministic term normalization，例如 `10 cm`、`10cm` 与“10厘米”；
2. 定义 Groundedness、Correctness、Completeness、Condition Handling、Safety Preservation 的可执行 human rubric；
3. 人工复核 `remote_start_blocked_answer_001` 的宽泛 answer contract；
4. 明确正式 V4 artifact 命名和冻结流程。

本轮没有调用 Ollama，没有运行正式 Answer Evaluation、retrieval evaluation 或索引 rebuild。
