# V4 Answer Evaluation Pre-Baseline Audit

## 1. 执行摘要

本次审计基于当前代码、当前 V3.5 BM25 chunk corpus、冻结的 `manual_eval_set.jsonl`、未提交的 Answer Evaluation 初版及其历史输出完成。没有运行新的答案生成，也没有修改 production RAG、retrieval benchmark、Answer Evaluation 数据或 evaluator。

结论：当前 Answer Evaluation **不具备建立可信 V4 formal baseline 的条件**。主要阻塞项如下：

1. `data/eval/answer_eval_set.jsonl` 实际是 12 个多行 JSON object 的连续流，不是 loader 所要求的“一行一个 JSON object”。当前 `load_answer_eval_cases()` 在第 1 行即失败。
2. 12 条 case 中有 5 条引用当前索引中不存在的旧 chunk，另有 4 条只完成了部分 V3.5 provenance 对齐。
3. Answer Evaluation artifact 只保存 post-processed answer 和 citation quote，不能重建 LLM 实际看到的完整 Evidence、Evidence ID、顺序、heading path 或截断状态。
4. Answer post-processing 的 broad regex 会破坏正常中文，例如把“具体操作应根据车辆状态进行。”改成“具体操作应车辆状态进行。”。
5. internal reference leak detector 漏检 `E3证据`、`E5 证据`、`参照E3证据`、`参考 E2 证据` 等历史报告中真实出现的形式。
6. human review schema 存在，但 0/1/2 没有可执行 rubric，历史输出全部为 TODO / null。

现有 `answer_eval_v1` 只能标记为 **pre-V4 diagnostic / pre-provenance-refresh**，不能作为正式 V4 baseline。

## 2. 当前 Answer Pipeline

当前真实调用链如下：

```text
question
  -> LocalEmbeddingClient.embed_query
  -> HybridRetriever.search(dense / bm25 / hybrid)
  -> retrieval-stage TOC/noise filtering + content dedup
  -> context_selection_pre filtering + dedup
  -> optional reranker (默认关闭时为 NoopReranker)
  -> metadata-aware select_contexts
  -> context_selection_post dedup
  -> optional neighbor expansion (当前默认关闭)
  -> final_context_pre_prompt filtering + dedup
  -> assemble_final_answer_contexts(count + char budget)
  -> build_answer_prompt
  -> OllamaClient.generate
  -> QAChain._post_process_answer
  -> QueryResponse(answer + citations)
  -> evaluate_answer_response
  -> Markdown / JSON Answer Evaluation artifact
```

当前关键配置：

- `DEFAULT_MAX_CONTEXTS = 5`
- `DEFAULT_MAX_CONTEXT_CHARS = 6000`
- QAChain 实际 context count 为 `min(top_k, 5)`
- QAChain 实际 char budget 为 `settings.MAX_CONTEXT_CHARS`，默认 `6000`
- `ENABLE_METADATA_CONTEXT_SELECTION = true`
- `ENABLE_NEIGHBOR_CONTEXT_EXPANSION = false`
- `ENABLE_RERANK = false`

## 3. Final Evidence Flow

### 3.1 Context identity alignment

QAChain 在 retrieval、selection、可选 expansion、final filtering/dedup 后调用 `assemble_final_answer_contexts()`。返回的同一个 `retrieved_chunks` list 同时用于：

1. 提取 `chunks` 并构造 prompt；
2. 构造 `QueryResponse.citations`。

因此，正常路径下 prompt Evidence 与 citations 的 **chunk identity 和顺序一致**。之前“prompt 看到 5 个 chunk、citations 返回更多 chunk”的问题已被 final assembly 修复。

### 3.2 Remaining representation gap

identity 一致不等于 evidence representation 完全一致：

- prompt 使用 chunk 的正文，最多 5 条、总 content 预算 6000 字符；
- citation 仅保存 `build_relevant_quote()` 生成的相关短 quote，默认上限 220 字符；
- citation 不保存 `heading_path`；
- artifact 不保存 Evidence ID、完整 prompt content、Evidence 顺序字段或 `truncated` 状态；
- QueryResponse 只包含 post-processed answer，不包含 raw LLM answer 或实际 prompt。

如果首个 chunk 自身超过 char budget，`assemble_final_answer_contexts()` 会保留整个 chunk，而 prompt builder 会对其尾部截断并添加 `[TRUNCATED]`。citation 仍只保存短 quote，artifact 无法知道模型看到的具体截断文本。

结论：当前 Answer Evaluation JSON **不能精确重建某次 generation 时 LLM 实际看到的全部 Evidence**。人工只看 citation quote 可能把实际有 Evidence 支撑的 claim 错判为 unsupported，也可能看不到 prompt 中导致污染的其他正文。这是 P0 blocker。

## 4. Prompt Evidence Representation

当前 prompt Evidence 格式为：

```text
[EVIDENCE E1]
page: ...
chapter: ...
section: ...
subsection: ...
heading_path: ...
content_type: ...
content:
...
[/EVIDENCE]
```

行为确认：

- Evidence ID 在最终顺序上动态生成 `E1`、`E2`……，不写入 Chunk schema；
- `subsection` 优先读取 `chunk.subsection`，其次读取 metadata，缺失时为 `N/A`；
- `heading_path` list 会格式化为 `chapter > section > subsection`，不会输出 Python list；
- 若 metadata 无 heading path，则回退至 chapter/section/subsection；
- Evidence 顺序保持 final contexts 的顺序；
- count budget 先执行，char budget 后执行；
- 后续 Evidence 完整加入会超预算时直接停止，不重新排序；
- 只有首个 Evidence 本身超预算时才截断，保留开头并标注 `[TRUNCATED]`。

Prompt 规则已覆盖 grounding、insufficient evidence、安全条件、条件差异/真正冲突、列表覆盖和禁止输出内部 Evidence ID。结构本身适合作为后续 baseline 输入，但 artifact 目前没有捕获该结构的实际实例。

## 5. Citation / Evidence Alignment

| 项目 | 当前状态 | 结论 |
| --- | --- | --- |
| Prompt 与 citation chunk identity | 同一 final context list | 对齐 |
| Prompt 与 citation 顺序 | 同一 list 顺序 | 对齐 |
| Prompt full text | 发送完整或首条截断正文 | artifact 未保存 |
| Citation quote | 最多约 220 字的 question-relevant quote | 不等于 prompt Evidence |
| Prompt Evidence ID | E1...En | artifact 未保存 |
| heading_path | prompt 有 | citation/artifact 无 |
| truncation | prompt 可标记 | artifact 未保存 |
| raw LLM answer | post-process 前存在于局部变量 | artifact 未保存 |

Formal baseline 前，应在 Answer Evaluation artifact 中保存“实际发送给 LLM 的 Evidence snapshot”，而不是根据 citation 反推。至少需要 evidence_id、chunk_id、实际发送 content、truncated、page、chapter、section、subsection、heading_path、content_type 和 order。

## 6. Answer Post-Processing Audit

当前 `_post_process_answer()` 依次执行：

```python
r"(参见|参考|根据)?\s*(手册片段|资料|片段|上下文|context|source id)\s*\d+\s*(中|里|内)?"
r"(参见|参考|根据)?\s*Evidence(?:\s*ID)?\s*E\d+\s*(中|里|内)?"
r"(参见|参考|根据)\s*[,，:：]?"
```

第三条 regex 不要求后面存在内部引用，因此会删除普通语义动词：

```text
输入：具体操作应根据车辆状态进行。
输出：具体操作应车辆状态进行。
```

实测其他边界：

| 输入 | 当前输出 | 判断 |
| --- | --- | --- |
| `参考 Evidence E2 执行。` | `执行。` | 内部引用被清理 |
| `根据[EVIDENCE E1]执行。` | `[]执行。` | 清理不完整并遗留括号 |
| `参照E3证据执行。` | 原样保留 | leak 未清理 |
| `见 E5 证据。` | 原样保留 | leak 未清理 |
| `车辆显示故障代码 E1` | 原样保留 | 正确保留业务文本 |

这是 P0 blocker：formal baseline 如果只保存 post-processed answer，将混合评估模型生成质量与清理器造成的文本损坏，同时无法追踪 raw answer。

## 7. Internal Evidence Leak Detection

当前 detector：

```python
r"Evidence(?:\s+ID)?\s+E\d+|\[EVIDENCE\s+E\d+\]|CONTEXT|source\s+id"
```

实测结果：

| 样例 | 结果 | 分类 |
| --- | --- | --- |
| `Evidence E1` | true | DETECTED |
| `[EVIDENCE E1]` | true | DETECTED |
| `根据Evidence E4` | true | DETECTED |
| `E1 Evidence` | false | MISSED |
| `E3证据` | false | MISSED |
| `E5 证据` | false | MISSED |
| `参照E3证据` | false | MISSED |
| `参考 E2 证据` | false | MISSED |
| `车辆显示故障代码 E1` | false | 正确避免 POTENTIAL_FALSE_POSITIVE |

历史 `answer_eval_v1.md` 中实际出现“证据 E2 和 E3”“参照E3证据”“与E5证据中的警告相吻合”，但 summary 仍显示 `internal_reference_leak_count = 0`。因此 detector defect 是 P0 blocker。修复时必须继续避免把裸 `E1` 视为 leak。

## 8. Answer Eval Dataset Overview

当前文件包含 12 个 dev cases。实际 schema 没有 `category` 字段，使用 `answer_type` 表示 procedure、warning、explanation、condition 或 insufficient_evidence。

字段包括：

- `id`
- `question`
- `answer_type`
- `must_include_terms`
- `must_include_points`
- `must_not_include_terms`
- `must_not_claim`
- `critical_warning_points`
- `expected_sections`
- `expected_subsections`
- `allow_insufficient_answer`
- `evidence`
- `source_case_id`
- `split`
- `notes`

文件扩展名为 JSONL，但当前 492 行内容是 12 个 pretty-printed JSON objects。`load_answer_eval_cases()` 按行 `json.loads(line)`，实测在 `data/eval/answer_eval_set.jsonl:1` 抛出 `Invalid JSONL`。现有评测脚本目前无法从该文件启动。

## 9. Per-Case Provenance Audit

当前索引检查基于 `data/processed/bm25_index.pkl` 中 981 个 indexed chunks 和 21 个 filtered chunks。冻结 retrieval benchmark validation 为 68 active、1 excluded、99 evidence、0 issues。

下表以 provenance 为主分类。`ANSWER_CONTRACT_REVIEW` 是可叠加标记，不用于重复计算 primary status 总数。

| Case | Source Case | Current Frozen Gold | Answer Eval Evidence | Status | Issue |
| --- | --- | --- | --- | --- | --- |
| `epb_enable_release_answer_001` | `epb_enable_release_001` | `a485...`, `dcdde...` | 两个 ID 均存在且 quote 匹配 | PROVENANCE_PARTIALLY_STALE | evidence 未记录当前 chapter/subsection/heading_path；预期 subsection 在 case 顶层存在 |
| `remote_key_start_answer_001` | `remote_key_start_001` | `a0a38...` | 旧 ID `17b921...` 不存在 | PROVENANCE_STALE | 当前 gold boundary/ID 已变化 |
| `pressure_wash_warning_answer_001` | `pressure_wash_warning_001` | `e02d2...` | 旧 ID `200ae...` 不存在 | PROVENANCE_STALE | 当前 section=`清洁车辆`、subsection=`高压冲洗`，旧 evidence 把高压冲洗作为 section |
| `abs_fault_warning_answer_001` | `abs_fault_handling_001` | `7ec788...` | ID 与 quote 均有效 | PROVENANCE_PARTIALLY_STALE | evidence 未记录当前 subsection=`功能状态说明` 与 heading_path |
| `abs_explanation_answer_001` | `abs_explanation_001` | `b6c394...` | ID、quote、page、section 一致 | PROVENANCE_CURRENT | 当前 chunk 无 subsection，与 case 一致 |
| `autohold_explanation_answer_001` | `autohold_explanation_001` | `4495a...` | ID、quote、page、section 一致 | PROVENANCE_CURRENT | Answer Eval evidence 与当前 chunk 对齐 |
| `overspeed_condition_answer_001` | `overspeed_alarm_001` | `4caecc...` | 旧 ID `6806aa...` 不存在 | PROVENANCE_STALE | 当前 gold ID/boundary 已变化 |
| `remote_start_blocked_answer_001` | `remote_start_blocked_001` | `5f81b...` | 旧 ID `7edbda...` 不存在 | PROVENANCE_STALE + ANSWER_CONTRACT_REVIEW | 当前 section=`通过手机APP启动车辆`、subsection=`通过网络远程启动发动机`；contract 未覆盖当前 evidence 中冷却液低、燃油低、车内有遥控钥匙等条件 |
| `epb_auto_subsection_answer_001` | `epb_enable_release_001` | source case gold 仅为启用/释放两个 chunks | `09c8e...` 当前存在且直接回答本题 | PROVENANCE_PARTIALLY_STALE | evidence 本身当前有效，但 source_case_id 映射到不同意图的 broad retrieval case；缺少 provenance metadata |
| `epb_poweroff_release_answer_001` | `epb_enable_release_001` | source case gold 仅为启用/释放两个 chunks | `a85a...`、`cf544...` 当前存在 | PROVENANCE_PARTIALLY_STALE | source_case_id 与具体特殊条件意图不匹配；缺少 subsection/heading_path；第一条 quote 末尾标点与当前 chunk 不一致 |
| `charging_led_list_answer_001` | `charging_led_states_001` | `adaf7...`, `66e0c...` | 旧 IDs `32cc6...`, `59e6d...` 均不存在 | PROVENANCE_STALE | 当前两个等价 gold 均独立覆盖完整 LED 状态；section/subsection 结构也已变化 |
| `unsupported_voice_brake_calibration_answer_001` | N/A | N/A | 无 evidence | HARD_NEGATIVE_CURRENT | 当前 981-chunk text corpus inspection 未发现语音校准制动的直接证据；仍需在 formal dataset 规则中记录 hard-negative 审核方法 |

Primary status 统计：

- PROVENANCE_CURRENT: 2
- PROVENANCE_STALE: 5
- PROVENANCE_PARTIALLY_STALE: 4
- HARD_NEGATIVE_CURRENT: 1
- AMBIGUOUS: 0
- ANSWER_CONTRACT_REVIEW: 1（叠加在 `remote_start_blocked_answer_001`）

## 10. Answer Contract Review

Retrieval gold 与 Answer contract 必须分开维护。当前 provenance stale 不自动意味着 `must_include_points` 应机械复制 frozen retrieval quote。

本轮发现的明确 contract review 项：

### `remote_start_blocked_answer_001`

当前 frozen evidence 包含：不在 P 挡、冷却液低、燃油低、车内有遥控钥匙、网络信号丢失、机舱盖/车门未锁、发动机故障、维修模式。现有 `must_include_points` 只覆盖其中一部分。需要人工决定该宽泛“哪些情况下”问题是否要求完整列举全部直接条件。

其他 case 的 semantic contract 暂未发现必须立即改写的明确证据，但 provenance refresh 时仍应逐条由手册事实复核，不能从当前模型答案反向调整。

## 11. Existing Pre-V4 Diagnostic Results

现有输出生成时间为 `2026-08-31T23:48:41`，早于 V3.5 frozen retrieval commits，且 citations 大量显示旧 chunk ID 和 `subsection=N/A`。它只能作为 pre-V4 diagnostic。

历史报告仍有诊断价值，暴露了以下典型 failure：

- EPB enable/release：把“手动紧急制动”混入一般启用步骤，并给出证据外的 D/R 挡轻踩油门释放描述；
- remote key start：将低电量紧急启动路径混入普通遥控钥匙启动；
- pressure wash：输出了 10/30 厘米，但 exact term check 因 `cm`/`厘米` 格式差异判 missing；
- ABS fault：漏掉“立刻在安全区域停车”，加入泛化故障排查和外部维修建议，并泄漏“证据 E2 和 E3”；
- EPB AUTO：把条件性结果扩写为不存在于 evidence 的操作步骤；
- EPB power-off release：泄漏 `参照E3证据`、`E5证据`；
- insufficient evidence：包含标准 fallback，因此 deterministic check pass，但随后继续补充语音助手常识和联系服务中心建议。

这些 failure 可用于设计 V4 rubric 和回归测试，但旧数值不能作为 formal baseline。

## 12. Deterministic Evaluator Reliability

### 12.1 较可靠的检查

- answer 是否为空；
- 明确、低歧义 forbidden literal 的直接命中；
- citation 中 exact/contains section、subsection 是否命中（只代表 context structure，不代表 answer grounded）；
- 标准 insufficient fallback 是否出现（只代表包含该短语）。

### 12.2 只能作为辅助 diagnostic 的检查

- `must_include_term_coverage`：当前为原始 substring matching，没有 normalization；
- `expected_evidence_hit_rate`：来自 citations 的 section/subsection，不证明回答使用了该 evidence；
- `insufficient_evidence_behavior`：只检查标准短语是否存在，无法发现 fallback 后继续 hallucinate；
- forbidden term：无法识别同义改写；
- `must_include_points`、`must_not_claim`、`critical_warning_points`：当前完全不自动评分，只展示给人工。

### 12.3 已确认的 false negative / false interpretation 风险

- 单位格式：`10 cm` vs `10cm` vs `10厘米`；`30 cm` vs `30厘米`；
- 空白和 OCR spacing：`Lynk & Co领克中心` vs `Lynk & Co 领克中心`；
- 英文大小写：`Auto Hold`、`AUTO HOLD`；
- 标点和全半角：`驻车挡（P）` vs `驻车挡(P)`；
- 同义表达和语序：`安全区域停车` vs `将车停在安全区域`；
- 只出现 fallback 短语但随后扩写 unsupported content，仍会被判 insufficient behavior pass。

这些属于 P1 evaluator correctness improvements，不应以放宽 gold contract 的方式解决。

## 13. Human Evaluation Schema

schema 已支持：

- Groundedness: 0/1/2
- Correctness: 0/1/2
- Completeness: 0/1/2
- Condition Handling: 0/1/2
- Safety Preservation: 0/1/2
- Unsupported Claim: bool
- Critical Safety Omission: bool
- Notes

但当前状态为：

- 所有字段默认 null；
- Markdown 显示 TODO / NOT REVIEWED；
- 没有定义 0、1、2 的判定边界；
- 没有说明某维度何时 N/A；
- 没有 evidence-level attribution 或 reviewer provenance；
- 没有 inter-reviewer consistency 约束。

因此 schema 形状存在，但 rubric 不足以支持可复现 human baseline。这是 formal baseline 前的 P0 工作。

## 14. Baseline Blockers

| Priority | Issue | Evidence | Required Before Baseline? |
| --- | --- | --- | --- |
| P0 | Answer dataset 不是合法 JSONL | loader 在第 1 行失败 | 是 |
| P0 | 5 stale + 4 partially stale provenance cases | 当前索引 ID/metadata/quote 对照 | 是 |
| P0 | Artifact 无法重建 LLM 实际 Evidence | 只保存 citation quote，不保存 prompt Evidence snapshot | 是 |
| P0 | Raw answer 未保存 | 只有 post-processed answer | 是 |
| P0 | Post-process broad regex 破坏正常中文 | “根据车辆状态”最小复现 | 是 |
| P0 | Leak detector 漏检实际泄漏形式 | `E3证据` / `E5 证据` 等均 false | 是 |
| P0 | Human score 无明确 rubric | schema 有字段但全部 TODO/null | 是，若 baseline 包含人工语义评分 |
| P0 | Remote-start answer contract 需人工复核 | 宽泛问题 contract 未覆盖当前 evidence 的全部条件 | 是，针对该 case |
| P1 | Deterministic term normalization 缺失 | `10 cm` / `10厘米` 已产生 false negative | 否，但应在解释 baseline 前修复 |
| P1 | Insufficient behavior 检查过宽 | fallback 后继续 hallucinate 仍 pass | 否，但指标不能作为质量结论 |
| P1 | Citation structure hit 易被误读 | 命中 context metadata 不等于答案 grounded | 否，需改报告命名/说明 |
| P1 | Artifact 缺少 reviewer/run provenance | 当前只有 config 和 result | 否，建议 formal baseline 前补充 |
| P2 | Semantic judge / LLM-as-judge | 当前未实现 | 否 |
| P2 | 更大 external benchmark | 当前仅 12 条 answer dev cases | 否 |
| P2 | 多 reviewer 一致性工具 | 当前未实现 | 否 |

## 15. Recommended V4 Implementation Sequence

基于本次审计，建议顺序为：

1. **V4.0 — Dataset validity + provenance refresh**
   - 把文件恢复为合法 JSONL；
   - 以 frozen V3.5 chunks 更新 5 stale 和 4 partially stale cases；
   - 单独人工裁决 `remote_start_blocked_answer_001` contract；
   - 增加 answer benchmark provenance validator，但不机械复制 retrieval gold。
2. **V4.1 — Evaluator correctness fixes**
   - 修复 internal leak detection，覆盖中文 `E3证据` 等形式且保留裸业务 `E1`；
   - 增加轻量 deterministic normalization；
   - 明确 insufficient fallback 后继续扩写的检查语义。
3. **V4.2 — Exact generation trace capture**
   - 保存实际 prompt Evidence snapshot、order、truncation、heading metadata；
   - 同时保存 raw answer 与 post-processed answer；
   - 保证 citations 可追溯到同一 final context list。
4. **V4.3 — Post-processing correctness**
   - 收窄 broad regex；
   - 用明确 internal marker 做最小清理；
   - 添加正常中文和内部引用的双向回归测试。
5. **V4.4 — Human rubric definition**
   - 为五个 0/1/2 维度定义可执行判定边界和 N/A 规则；
   - 定义 Unsupported Claim 与 Critical Safety Omission 的证据要求。
6. **V4.5 — Formal answer baseline**
   - 固定 dataset、config、model、evidence trace 和 reviewer rubric 后再生成；
   - 旧 `answer_eval_v1` 保留为 pre-V4 diagnostic，不与新 baseline 直接比较。
7. **V4.6 — Failure taxonomy and answer quality improvements**
   - 区分 retrieval、context contamination、generation、post-process、evaluation defects；
   - 只有在 formal baseline 证明必要后，才修改 prompt 或 QA behavior。

下一步最小实现任务应是 **V4.0：修复 Answer Eval JSONL 有效性，并建立基于 frozen V3.5 chunks 的 provenance refresh/validation**。在该任务中仍不应修改 prompt、QAChain 或 production retrieval。

## 16. Audit Boundary

本次审计：

- 未调用 Ollama；
- 未生成新答案；
- 未运行新的 retrieval experiment；
- 未 rebuild index；
- 未修改 parser、splitter、retrieval、rerank、QAChain、prompt 或 post-processing；
- 未修改 retrieval benchmark；
- 未修改 Answer Evaluation dataset/evaluator/report；
- 仅新增本审计报告。
