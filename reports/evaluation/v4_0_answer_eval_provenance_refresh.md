# V4.0 Answer Evaluation 数据集与证据来源刷新报告

## 1. 执行摘要

本轮完成了 V4 formal baseline 前的 Answer Evaluation 数据集修复与 evidence provenance 刷新：

- `data/eval/answer_eval_set.jsonl` 已规范为一行一个 JSON object 的合法 JSONL；
- 12 条 case 及其 ID 全部保留；
- 11 条正向 case 的 19 条 evidence 已与冻结的 V3.5 chunk corpus 对齐；
- 1 条 hard negative 保持无 evidence，并通过专门规则校验；
- provenance validation 结果为 0 issue；
- 未修改任何 semantic answer contract 字段；
- 未修改 production RAG、QAChain、prompt、retrieval benchmark 或冻结报告；
- 未调用 Ollama，未运行正式 Answer Evaluation baseline，也未重建索引。

刷新后不再存在 `PROVENANCE_STALE` 或 `PROVENANCE_PARTIALLY_STALE` case。formal baseline 仍被 post-processing、最终 Evidence 精确快照和 internal Evidence leak detection 等既有 P0 问题阻塞。

## 2. 数据集格式修复

原文件虽然使用 `.jsonl` 扩展名，但包含 12 个跨多行 pretty-printed JSON object，逐行 loader 会在第一行失败。本轮将其规范化为 UTF-8 单行 JSONL：

- 每行一个完整 JSON object；
- 共 12 行、12 条 case；
- case ID 集合不变；
- 字段未删除；
- semantic answer contract 未因重新序列化而改变。

保留的 case ID：

1. `epb_enable_release_answer_001`
2. `remote_key_start_answer_001`
3. `pressure_wash_warning_answer_001`
4. `abs_fault_warning_answer_001`
5. `abs_explanation_answer_001`
6. `autohold_explanation_answer_001`
7. `overspeed_condition_answer_001`
8. `remote_start_blocked_answer_001`
9. `epb_auto_subsection_answer_001`
10. `epb_poweroff_release_answer_001`
11. `charging_led_list_answer_001`
12. `unsupported_voice_brake_calibration_answer_001`

## 3. Provenance Schema

现有 `EvalEvidence` 已能表达 V3.5 provenance，本轮没有扩展 schema。每条 evidence 使用以下字段：

- `chunk_id`
- `quote`
- `page`
- `chapter`
- `section`
- `subsection`
- `heading_path`

Answer Eval case 继续使用 `source_case_id` 关联冻结的 retrieval case。该关联用于确认来源 case 存在且处于 active 状态，但 retrieval gold 与 answer truth 保持分离：Answer Evaluation evidence 必须直接支撑回答契约，不要求机械复制 source retrieval case 的全部 ANY_OF gold。

## 4. 逐 Case 刷新结果

| Case | 刷新前状态 | 刷新后状态 | Source Case | 旧 Chunk | 当前 Chunk | 变更说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `epb_enable_release_answer_001` | `PROVENANCE_PARTIALLY_STALE` | `CURRENT_VALIDATED` | `epb_enable_release_001` | `a485ba75...`, `dcdde351...` | 同左 | 补齐 chapter、subsection、heading_path，并按当前 chunk 校准 quote。 |
| `remote_key_start_answer_001` | `PROVENANCE_STALE` | `CURRENT_VALIDATED` | `remote_key_start_001` | `17b921...` | `a0a38bbc...` | 更新 chunk ID、当前 metadata 和 quote。 |
| `pressure_wash_warning_answer_001` | `PROVENANCE_STALE` | `CURRENT_VALIDATED` | `pressure_wash_warning_001` | `200ae...` | `e02d2d11...` | 更新 chunk boundary/ID；section 为“清洁车辆”，subsection 为“高压冲洗”；使用 5 条当前原文覆盖完整 warning context。 |
| `abs_fault_warning_answer_001` | `PROVENANCE_PARTIALLY_STALE` | `CURRENT_VALIDATED` | `abs_fault_handling_001` | `7ec78836...` | 同左 | 补齐 subsection“功能状态说明”和 heading_path。 |
| `abs_explanation_answer_001` | `PROVENANCE_CURRENT` | `CURRENT_VALIDATED` | `abs_explanation_001` | `b6c3943e...` | 同左 | provenance 无语义变化，按当前 corpus 完整复核。 |
| `autohold_explanation_answer_001` | `PROVENANCE_CURRENT` | `CURRENT_VALIDATED` | `autohold_explanation_001` | `4495a19a...` | 同左 | provenance 无语义变化，按当前 corpus 完整复核。 |
| `overspeed_condition_answer_001` | `PROVENANCE_STALE` | `CURRENT_VALIDATED` | `overspeed_alarm_001` | `6806aa...` | `4caecc96...` | 更新 chunk ID、当前 metadata 和 quote。 |
| `remote_start_blocked_answer_001` | `PROVENANCE_STALE` + `ANSWER_CONTRACT_REVIEW` | `CURRENT_VALIDATED` + `ANSWER_CONTRACT_REVIEW` | `remote_start_blocked_001` | `7edbda...` | `5f81b96e...` | 更新 chunk ID；section 改为“通过手机APP启动车辆”，subsection 改为“通过网络远程启动发动机”，补齐 heading_path 和当前完整 quote。 |
| `epb_auto_subsection_answer_001` | `PROVENANCE_PARTIALLY_STALE` | `CURRENT_VALIDATED` | `epb_enable_release_001` | `09c8e7d1...` | 同左 | 补齐 EPB AUTO subsection provenance；该 answer evidence 已独立验证，不机械受 broad source case 的 ANY_OF gold 限制。 |
| `epb_poweroff_release_answer_001` | `PROVENANCE_PARTIALLY_STALE` | `CURRENT_VALIDATED` | `epb_enable_release_001` | `a85aeb24...`, `cf544339...` | 同左 | 补齐 subsection/heading_path，校准标点和当前 quote；procedure 与相邻 warning 共同支撑 answer contract。 |
| `charging_led_list_answer_001` | `PROVENANCE_STALE` | `CURRENT_VALIDATED` + `MULTI_GOLD_REVIEW_RESOLVED` | `charging_led_states_001` | `32cc6...`, `59e6d...` | canonical `adaf7b26...` | 采用 page 292 的完整 canonical evidence；page 295 的 `66e0c695...` 是冻结 retrieval benchmark 中内容完整且等价的 ANY_OF gold。 |
| `unsupported_voice_brake_calibration_answer_001` | `HARD_NEGATIVE_CURRENT` | `HARD_NEGATIVE_VALIDATED` | N/A | N/A | N/A | 保持无 evidence、无 source case，并要求 `allow_insufficient_answer=true`。 |

刷新分类汇总：

- `CURRENT_NO_CHANGE`：2 条；
- `UPDATE_CHUNK_ID`：4 条（其中 pressure wash 同时涉及 boundary/quote）；
- `UPDATE_METADATA`：6 条；
- `UPDATE_BOUNDARY_OR_QUOTE`：多条 evidence 按当前 chunk 原文校准，其中 pressure wash 为主要边界变化；
- `MULTI_GOLD_REVIEW`：1 条，已采用 canonical answer evidence；
- `HARD_NEGATIVE_CURRENT`：1 条；
- `ANSWER_CONTRACT_REVIEW`：1 条叠加标记；
- `PROVENANCE_STALE`：0 条；
- `PROVENANCE_PARTIALLY_STALE`：0 条。

分类允许叠加，因此汇总数字不用于相加得到 case 总数。

## 5. Multi-Gold 处理

`charging_led_list_answer_001` 对应的冻结 retrieval case 有两个语义等价、各自完整的 ANY_OF gold：

- page 292：`adaf7b26-e2fc-54d2-b885-d57a0bbb39c4`
- page 295：`66e0c695-609e-5b72-b7a6-4025e3606124`

Answer Evaluation 不机械复制全部 retrieval gold。本轮选择 page 292 chunk 作为 canonical provenance，因为单个 chunk 已完整覆盖蓝色、绿色、红色和橙色 LED 状态。等价 source chunk 记录在 notes 中，避免把 duplicate-equivalent retrieval target 错误解释为必须组合的 multi-hop answer evidence。

## 6. Hard Negative 处理

`unsupported_voice_brake_calibration_answer_001` 是 hard negative：当前手册证据中没有“通过语音命令校准制动系统”的直接依据。

校验规则允许该 case：

- `answer_type=insufficient_evidence`；
- `allow_insufficient_answer=true`；
- `evidence=[]`；
- `source_case_id=null`。

validator 不要求为 hard negative 伪造普通 positive evidence。

## 7. Answer Contract Review

需要后续人工复核的 case 为 `remote_start_blocked_answer_001`。

- Question：哪些情况下无法远程启动发动机？
- 当前 `must_include_points`：不在 P 挡、网络信号丢失、机舱盖或车门未锁定、发动机故障或维修模式；
- 当前 `must_not_claim`：不得把禁止条件描述成远程启动操作步骤；
- 当前 manual truth 还包含：冷却液液位较低、燃油油位较低、车内有遥控钥匙；
- Review 原因：问题是宽泛的“哪些情况下”，但现有 contract 未覆盖当前完整列表。

本轮仅刷新 provenance，未自动扩大 `must_include_terms` 或 `must_include_points`。后续应单独决定该宽泛问题是否要求完整列举所有直接条件，不能借 provenance 刷新机械改写 answer contract。

## 8. Validation 规则

新增的 fail-fast validation 检查：

1. Answer Eval case ID 唯一；
2. 正向 case 的 `source_case_id` 存在于冻结 retrieval dataset 且未被 excluded；
3. 正向 case 至少包含一条 evidence；
4. evidence 引用的 `chunk_id` 存在于当前 V3.5 corpus；
5. `quote` 非空，且在规范化空白后能够从当前 chunk text 中匹配；
6. `page`、`chapter`、`section`、`subsection` 与当前 chunk 精确一致；
7. `heading_path` 与当前 chunk 精确一致；
8. hard negative 必须允许不足证据回答且不得伪造 evidence；
9. 任一问题均通过明确异常 fail-fast，不会被静默计入 formal baseline。

校验不读取 retriever top-1 或排序结果来决定 provenance，避免 evaluation leakage。

当前 validation 结果：

```text
answer_eval_cases=12
positive_cases=11
hard_negative_cases=1
answer_evidence=19
provenance_valid=True
issue_counts={}
```

## 9. 测试结果

定向测试命令：

```bash
.venv/bin/python -m pytest tests/test_answer_evaluator.py tests/test_answer_provenance_validation.py -q
```

结果：`19 passed`。

覆盖范围包括：合法 JSONL、12 个 ID、duplicate ID、有效 provenance、缺失 source case、stale chunk ID、page/section/subsection/heading_path/quote 不一致、hard negative，以及 multi-gold source 使用 canonical answer evidence。

完整测试与语法检查结果见本轮最终执行记录。

## 10. Remaining Baseline Blockers

本轮完成后仍不能运行可信的 V4 formal baseline，至少还有以下既有阻塞项：

1. Answer post-processing 的 broad regex 会误删正常中文中的“根据/参考”等业务文本；
2. Answer Evaluation artifact 尚未保存 generation 时实际发送给 LLM 的完整 Evidence snapshot、Evidence ID、顺序和截断状态；
3. internal Evidence reference leak detector 漏检 `E3证据`、`参考 E2 证据` 等历史真实形式；
4. deterministic term normalization 仍可能把 `cm` 与“厘米”等等价表达判为缺失；
5. human scoring 的 0/1/2 rubric 尚未形成可执行标准；
6. `remote_start_blocked_answer_001` 的宽泛 answer contract 仍需人工复核。

## 11. 下一项建议

下一项最小任务应优先修复 Answer post-processing 与 internal Evidence leak detection，并增加 raw answer / post-processed answer 的可审计边界测试。随后再设计最终 Evidence snapshot artifact；在这些 P0 阻塞项消除前，不应运行或发布 V4 formal baseline。
