# V4.6-B Condition Preservation 受控实验报告

## 1. Executive Summary

本实验以固定生成配置建立 R0 reference，只在 T1 中增加一条通用 Condition Preservation 规则。R0 与 T1 的 dataset、evaluation semantics、retrieval、context、模型、Ollama runtime、temperature、seed、stream 以及每条 case 的 Prompt Evidence identity/order/text 均一致。

两个 primary target 的已知错误均未消除：`epb_poweroff_release_answer_001` 仍遗漏第一条路径的“关闭 EPB AUTO”前置条件；`remote_key_start_answer_001` 的 T1 答案与 R0 完全相同，仍把仅适用于钥匙电量低且无法识别时的杯托步骤列为普通启动第一步。根据 V4.6-A 预先冻结的 reject criteria，“两个 target 均无可复核改善”应判为无收益。

**EXPERIMENT_DECISION = REJECT**  
**MERGE_RECOMMENDED = NO**  
**V4_6_RESUME_READY_OPTIMIZATION_SUFFICIENT = NO**

人工 rubric 分数仅为 Codex proposed review，不是 final human adjudication；但本次 REJECT 不依赖模糊评分边界，而是基于两个预定义 condition failure 均客观保留。

## 2. Experiment Hypothesis

在 retrieval、ranking、context selection、answer model、generation parameters、evaluation semantics 和 dataset 全部不变时，仅加入通用 Condition Preservation generation policy，是否能同时：

1. 让操作路径保留 Evidence 中明确的 prerequisite；
2. 防止 special/emergency/fallback instruction 被泛化为 normal/default operation；
3. 保持七条 Human Full Pass regression guards。

## 3. Resume-Ready Relevance

这是 Resume-Ready 收敛阶段的单变量实验，不以提高全部 12-case 指标为目标。实验完成了 failure analysis -> hypothesis -> controlled intervention -> paired evaluation -> merge decision 的闭环。由于干预无目标收益，不应为了已有实现继续调词或强行合并。

## 4. Git / Branch State

- Branch：`exp/v4.6-condition-preservation`
- Base commit：`e86728dcaa803f5de8add2d620be3bfdcd6f6fe4`
- Base subject：`map v4.6 answer failures and experiment strategy`
- V4.5.1 commit：`12d6f4e make answer generation reproducible`
- R0/T1 运行时 worktree 为 dirty；原因包括实验 metadata 支持和既有未提交文件，已在 artifact 中记录 `git_worktree_dirty=true`。
- 实验前已存在且未触碰的 tracked changes：`AGENTS.md`、`README.md`、`app/core/exceptions.py`、`docs/evaluation.md`。
- 历史 untracked docs/reports 保持原状，未清理、未暂存、未提交。

## 5. Frozen Variables

| Variable | R0 | T1 | Equal |
| --- | --- | --- | --- |
| Dataset SHA-256 | `c3b06add0f3a906597a652997f824cd3c3cccc2e30eda684d6a98761ba493f8a` | same | YES |
| Evaluation semantics | `v4.3` | `v4.3` | YES |
| Retrieval mode | hybrid | hybrid | YES |
| Rerank | false | false | YES |
| top_k | 5 | 5 | YES |
| Metadata context selection | true | true | YES |
| Neighbor expansion | false | false | YES |
| max_contexts | 5 | 5 | YES |
| max_context_chars | 6000 | 6000 | YES |
| Embedding | `BAAI/bge-small-zh-v1.5` | same | YES |
| Answer model | `qwen2.5:7b` | same | YES |
| Model digest | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | same | YES |
| Ollama | `0.33.2` | `0.33.2` | YES |
| stream | false | false | YES |
| temperature | 0.0 | 0.0 | YES |
| seed | 42 | 42 | YES |
| timeout | 120 seconds | 120 seconds | YES |

Ollama/model defaults 仍控制 `top_k`、`top_p`、`min_p`、`repeat_penalty`、`num_predict` 和 `num_ctx`；R0/T1 对这些 inherited options 的来源记录一致。

## 6. Independent Variable

唯一 intentional production variable 是 answer prompt 中新增的一条通用 Condition Preservation contract。实验 metadata 参数与 prompt hash 记录能力在 R0 前加入 evaluator，R0/T1 共用，不属于 treatment variable。

## 7. R0 Controlled Reference

- JSON：`reports/evaluation/v4_6_b_condition_preservation_reference_20260903_001.json`
- Markdown：`reports/evaluation/v4_6_b_condition_preservation_reference_20260903_001.md`
- experiment_id：`v4.6-b-condition-preservation`
- experiment_phase：`reference`
- Prompt SHA-256：`1c2ebcf4ee6f67d84e71c6dc7f29a670d017fcbfb80528c2f105d36fe4d9cdc0`
- Cases：12
- Average elapsed：9.6782 seconds/case

R0 是 fixed-generation controlled reference，不覆盖、不替代 V4.4 inherited-default historical baseline。

## 8. R0 Integrity Check

| Gate | Result |
| --- | --- |
| REFERENCE_GENERATION_COMPLETE | YES |
| REFERENCE_FIXED_GENERATION_CONFIG | YES |
| REFERENCE_DATASET_MATCH | YES |
| REFERENCE_SEMANTICS_MATCH | YES |
| REFERENCE_RETRIEVAL_CONFIG_MATCH | YES |

## 9. Exact Condition Preservation Intervention

干预要求：Evidence 中的操作、警告或结论如果只适用于明确的前提、状态、模式、故障、例外或回退情形，回答必须保留适用条件，不得把条件性内容表述为无条件的一般规则；程序前置条件必须与对应步骤一起说明。

该规则不包含 EPB、遥控钥匙、杯托或其他 case-specific 名称，也不改变 answer scope、context formatting、groundedness、safety、citation 或 insufficient-evidence policy。

## 10. Exact Prompt Delta

原规则 4 的已有冲突处理文本保持不变，仅在末尾追加：

> Evidence 中的操作、警告或结论如果只适用于明确的前提、状态、模式、故障、例外或回退情形，回答必须保留该适用条件，不得将条件性内容表述为无条件的一般规则；程序所需的前置条件必须与对应步骤一起说明。

没有新增“只回答必要内容”“保持简短”等 Answer Scope 条款。

## 11. T1 Treatment

- JSON：`reports/evaluation/v4_6_b_condition_preservation_treatment_20260903_001.json`
- Markdown：`reports/evaluation/v4_6_b_condition_preservation_treatment_20260903_001.md`
- experiment_id：`v4.6-b-condition-preservation`
- experiment_phase：`treatment`
- Prompt SHA-256：`87849928b0d76794a9474205c4aa6a7d32272e775b733c8de24e452eb4743f58`
- Cases：12
- Average elapsed：9.3864 seconds/case

## 12. Causal Isolation Matrix

| Check | Result | Notes |
| --- | --- | --- |
| DATASET_HASH_EQUAL | YES | 同一 12-case dataset |
| SEMANTICS_VERSION_EQUAL | YES | `v4.3` |
| RETRIEVAL_CONFIG_EQUAL | YES | hybrid, top_k=5 |
| RERANK_CONFIG_EQUAL | YES | false |
| CONTEXT_CONFIG_EQUAL | YES | selection/budget/neighbor 全部一致 |
| MODEL_IDENTITY_EQUAL | YES | `qwen2.5:7b` |
| MODEL_DIGEST_EQUAL | YES | digest exact match |
| OLLAMA_VERSION_EQUAL | YES | `0.33.2` |
| TEMPERATURE_EQUAL | YES | 0.0 |
| SEED_EQUAL | YES | 42 |
| STREAM_EQUAL | YES | false |
| PROMPT_EVIDENCE_IDENTITY_ORDER_TEXT_EQUAL | YES | 12/12 exact match |
| EXPECTED_TREATMENT_DELTA_PRESENT | YES | prompt hash 和规则文本按设计改变 |
| UNEXPECTED_VARIABLE_DELTA | NO | 未发现 |

因果隔离有效。答案差异可以归因于 prompt policy delta 与模型在该 delta 下的生成响应；不能归因于 Evidence 变化。

## 13. Target Case: `epb_poweroff_release_answer_001`

### Evidence situation

R0/T1 的 E1 完整包含两条释放路径。第一条明确要求先在中央显示屏关闭 EPB AUTO；E5 包含释放状态下防止溜车的警告。Evidence identity/order/text exact match。

### R0 vs T1

| Item | R0 | T1 |
| --- | --- | --- |
| 特殊场景范围 | 保留洗车/牵引 | 保留洗车/牵引 |
| 第一条路径“关闭 EPB AUTO” | 遗漏 | **仍遗漏** |
| 第二条路径 | 保留 | 保留 |
| 防溜车警告 | 保留 | 保留 |
| 实质变化 | - | 仅“应时刻注意”变为“应注意” |

Codex proposed rubric（不是 final human adjudication）：

| Phase | Groundedness | Correctness | Completeness | Condition Handling | Safety | Unsupported | Critical Omission |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| R0 | 1 | 0 | 1 | 0 | 2 | true | false |
| T1 | 1 | 0 | 1 | 0 | 2 | true | false |

目标要求 `T1 Condition Handling >= R0 + 1` 未满足，known prerequisite omission 未消除。

## 14. Target Case: `remote_key_start_answer_001`

### Evidence situation

E1 是钥匙电量低且无法检测时的紧急启动流程；E2 是普通遥控钥匙启动流程。R0/T1 的 Evidence identity/order/text exact match。

### R0 vs T1

R0 与 T1 final answer **逐字相同**。两者都把“将遥控钥匙放入前杯托底部”列为普通启动第一步，之后才在说明中恢复其紧急适用条件。

Codex proposed rubric（不是 final human adjudication）：

| Phase | Groundedness | Correctness | Completeness | Condition Handling | Safety | Unsupported | Critical Omission |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| R0 | 1 | 0 | 2 | 0 | 2 | true | false |
| T1 | 1 | 0 | 2 | 0 | 2 | true | false |

目标要求 `T1 Condition Handling >= R0 + 1` 未满足，special-to-general promotion 未消除。

## 15. Seven Regression Guards

以下均为 Codex proposed review，不替代用户 final human adjudication。

| Guard | R0 key behavior | T1 key behavior | Proposed R0/T1 result |
| --- | --- | --- | --- |
| `pressure_wash_warning_answer_001` | 距离、底部接插件、发动机舱、制动水汽均保留 | 同样保留；列表措辞轻微调整 | Full Pass / Full Pass |
| `overspeed_condition_answer_001` | 触发与解除方向正确 | 与 R0 完全相同 | Full Pass / Full Pass |
| `remote_start_blocked_answer_001` | canonical conditions 完整覆盖 | 同一条件集合，尾句增加条件总括 | Full Pass / Full Pass |
| `abs_explanation_answer_001` | ABS 作用与正常反馈准确 | 仅轻微措辞变化 | Full Pass / Full Pass |
| `autohold_explanation_answer_001` | 短暂停车与释放关系正确 | 与 R0 完全相同 | Full Pass / Full Pass |
| `charging_led_list_answer_001` | 8 种 LED 状态完整，红灯处理保留 | 8 种状态和处理均保留 | Full Pass / Full Pass |
| `unsupported_voice_brake_calibration_answer_001` | 明确拒绝无依据校准步骤 | 继续拒绝，没有拼接伪步骤 | Full Pass / Full Pass |

Proposed guard result：7/7 在 R0 和 T1 均保持 Human Full Pass；未发现 completeness-sensitive list 或 hard-negative regression。

## 16. Non-Target Secondary Observations

- `epb_enable_release_answer_001`：T1 仍把紧急制动描述为“启用 EPB”的主要方法，正常启用 Evidence 仍缺失；无 secondary positive effect。
- `abs_fault_warning_answer_001`：专用“安全区域停车” Evidence 仍不在 Prompt，答案继续产生弱依据流程；不属于本实验修复范围。
- `epb_auto_subsection_answer_001`：核心结论正确，但继续扩展 P 挡、手动 EPB 和 START/STOP 程序；Condition Preservation 没有解决 Answer Scope 问题。

## 17. Automated Metrics Comparison

| Metric | R0 | T1 | Delta |
| --- | ---: | ---: | ---: |
| case_count | 12 | 12 | 0 |
| answer_non_empty_pass | 12 | 12 | 0 |
| internal_reference_leak_count | 0 | 0 | 0 |
| forbidden_term_failure_count | 0 | 0 | 0 |
| must_include_term_average_coverage | 0.8535 | 0.8535 | 0.0000 |
| expected_evidence_hit_rate | 0.3636 | 0.3636 | 0.0000 |
| insufficient_evidence_behavior_pass_rate | 1.0000 | 1.0000 | 0.0000 |
| average_elapsed_seconds | 9.6782 | 9.3864 | -0.2918 |

Elapsed 是各自单次离线运行记录，不是正式 latency benchmark，也不用于本实验决策。

## 18. Proposed Human Paired Review

建议用户仅需确认以下 paired facts，而不必重新开放 V4.5-C frozen labels：

1. EPB 第一条路径在 T1 中是否仍遗漏“关闭 EPB AUTO”：**proposed YES**。
2. 杯托步骤在 T1 中是否仍被列为普通启动第一步：**proposed YES**。
3. 两个 target 的 Condition Handling 是否至少提升 1 分：**proposed NO / NO**。
4. 七条 guards 是否仍为 Full Pass：**proposed 7/7 YES**。

这些是 experiment-level proposed scores，不写回 V4.5-C artifact。

## 19. Unsupported Claim Analysis

- 两个 target 的既有 unsupported behavior 均未消除。
- 七条 guards 未发现新增 Unsupported Claim。
- 自动 forbidden-term failures 为 R0=0、T1=0；该代理指标不能替代人工 groundedness 判断。

## 20. Safety Regression Analysis

- EPB target 的防溜车警告在 R0/T1 均保留。
- Pressure-wash guard 的距离和禁止事项保留。
- 未发现 T1 新增 Critical Safety Omission。
- ABS fault 的历史 critical safety omission 仍存在，但其专用 Evidence 不在 Prompt，且它不是本实验 target；不能把未改善判为 treatment 新回归。

## 21. Completeness Regression Analysis

- `remote_start_blocked_answer_001` 的 exhaustive conditions 保持。
- `charging_led_list_answer_001` 的 8 种 LED 状态保持。
- 未发现新的列表完整性回归。
- EPB poweroff target 的既有 prerequisite omission 仍存在，因此 target completeness 没有改善。

## 22. Case-Specific Hack Check

**CASE_SPECIFIC_HACKS_PRESENT = NO**。

规则只描述 prerequisite、state、mode、fault、exception 和 fallback applicability，没有出现目标车型功能名称或问题专用分支。实验失败不能通过继续添加 EPB/遥控钥匙特例补救。

## 23. ACCEPT / REJECT / INCONCLUSIVE

**EXPERIMENT_DECISION = REJECT**。

理由：V4.6-A 在实现前明确把“两个 target 均无可复核改善”列为 Reject Criteria。本次两个目标的 known condition failure 均完整保留，且 target Condition Handling proposed delta 均为 0。因果隔离成立，因此不是配置漂移导致的 inconclusive；七条 guards 未退化也不能抵消 treatment 对目标无效。

## 24. Merge Recommendation

**MERGE_RECOMMENDED = NO**。

不建议把 prompt delta 合并到 main。实验 metadata 支持是否保留，应在提交边界审查时与 rejected production policy 分开处理；本报告和 R0/T1 artifacts 应作为有效的负实验结果保留。

## 25. Known Limitations

- 只有 12 条 dev diagnostic cases，不能解释为 production accuracy。
- Proposed human scores 尚待用户确认；它们不是 final human adjudication。
- 单次 R0/T1 不构成统计显著性结论，但 V4.5.1 已在固定环境验证 repeated-run exact-output stability。
- 本实验没有诊断为何模型忽略新增规则，只能确认该最小 wording 在当前模型/上下文下无目标收益。
- Ollama 的部分 generation options 继续继承模型或服务默认值，但 R0/T1 环境和记录一致。

## 26. Resume-Ready Gate Impact

**V4_6_RESUME_READY_OPTIMIZATION_SUFFICIENT = NO**。

Condition Preservation 的最小单规则干预未修复目标失败，不应自动继续微调同一规则。是否在 Resume-Ready 前再做最多一个高 ROI experiment，需要单独人工决策；本实验本身不支持把 Answer Scope 或 Context Selection 自动纳入下一步。

## 27. Global Project Information Sync Audit

| Information surface | Decision | Reason |
| --- | --- | --- |
| `README.md` | NO_UPDATE_NEEDED | T1 被拒绝，不能描述为稳定能力；既有 dirty change 不属于本实验 |
| `AGENTS.md` | NO_UPDATE_NEEDED | 已有 controlled experiment 治理；不为一次 rejected treatment 改长期规则 |
| `docs/evaluation.md` | NO_UPDATE_NEEDED | Frozen semantics 未变化；既有 dirty change 不属于本实验 |
| `.env.example` / config docs | NO_UPDATE_NEEDED | 无配置变化 |
| Tests | UPDATE_REQUIRED, completed | 增加 generic policy 和 experiment metadata deterministic tests |
| Evaluation reports | UPDATE_REQUIRED, completed | 新增 R0、T1 与本报告 |
| Production comments/docstrings | NO_UPDATE_NEEDED | 无架构或接口变化 |

## 28. Next Step

1. 用户确认 paired human review 的两个 target 和七个 guards。
2. 不合并 Condition Preservation prompt delta；不要继续围绕同一句规则做 case-driven wording tuning。
3. 保留负实验 artifacts 和报告。
4. 是否进行最多一个 Answer Scope experiment，或直接结束 V4.6 并转入后续阶段，由用户基于 Resume-Ready 优先级明确决定；本任务不启动任何后续实验。

最终 flags：

- `R0_INTEGRITY_GATE = YES`
- `CAUSAL_ISOLATION_VALID = YES`
- `PRIMARY_TARGET_SUCCESS = NO`
- `REGRESSION_GUARDS_PRESERVED_PROPOSED = YES`
- `CASE_SPECIFIC_HACKS_PRESENT = NO`
- `EXPERIMENT_DECISION = REJECT`
- `MERGE_RECOMMENDED = NO`
- `V4_6_RESUME_READY_OPTIMIZATION_SUFFICIENT = NO`
