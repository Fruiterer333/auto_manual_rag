# V4.6-A Failure-to-Intervention Mapping 与实验设计

## 1. Executive Summary

V4.6-A 只进行根因分析、干预映射和受控实验设计，没有修改 production RAG、Prompt、retrieval、context selection、rerank、模型或评测语义。

冻结的 V4.5 人工裁决显示，12 条 dev diagnostic cases 中 Human Full Pass 为 7/12（58.33%）。主要失败归因分布为 GENERATION=4、RETRIEVAL=1、NONE=7；`GENERATION_GROUNDING_FAILURE`、`CONDITION_HANDLING_FAILURE` 和 `UNSUPPORTED_EXTRAPOLATION` 各出现 4 次。该证据支持优先研究 generation 对适用条件和回答范围的保持，但不支持直接断言“Prompt 是唯一根因”或“必须更换模型”。

首个 V4.6-B 单变量实验建议为 **Condition Preservation**。它针对两条高置信 generation failures：正确 Evidence 已进入 Prompt，但前置条件被遗漏或特殊条件被提升为默认步骤。Answer Scope 作为第二个独立候选实验；Context Selection 暂不修改，因为 ABS 与 EPB 互补证据缺失的中间链路 trace 不完整，且与 Prompt-policy 同时修改会破坏归因。

## 2. Frozen Evidence Base

本报告使用以下冻结或已验证 artifact：

- `reports/evaluation/v4_answer_baseline_hybrid_no_rerank_20260902_200054.json`：V4.4 exact Prompt Evidence、raw/final answer、citations 和历史运行配置。
- `reports/evaluation/v4_5_c_human_adjudicated_baseline.json`：12 条最终人工裁决及 failure taxonomy。
- `reports/evaluation/v4_5_c_human_adjudication_summary.md`：人工聚合指标、ABS 事后 evidence audit 和 multi-gold limitation。
- `data/eval/answer_eval_set.jsonl`：问题合同与 canonical evidence provenance。
- `reports/evaluation/v3_5_frozen_hybrid_no_rerank.json`：冻结 hybrid no-rerank top-5 retrieval 结果。
- `reports/evaluation/v3_5_frozen_hybrid_rerank.json`：冻结 hybrid + rerank top-5 retrieval 结果，只用于理解历史 candidate/rank 行为，不作为 V4.6 解法。
- `reports/evaluation/v4_5_1_generation_stability.json`、`.md` 与 `v4_5_1_generation_reproducibility.md`：固定 generation configuration 下的 repeated-run stability 证据。

V4.4 历史基线为 12 cases（11 positive、1 hard negative），配置是 hybrid、rerank=false、top_k=5、metadata selection=true、neighbor expansion=false、max_contexts=5、max_context_chars=6000、`qwen2.5:7b`、semantics `v4.3`。其 temperature/seed 未显式发送，必须继续视为 inherited-default historical baseline，不能改写成 fixed-generation baseline。

## 3. Repository / Branch State

- 当前 branch：`main`。
- V4.5.1 独立 commit：`12d6f4e make answer generation reproducible`。
- 本任务开始前存在一个与 V4.6-A 无关的 tracked change：`app/core/exceptions.py`。
- 本任务开始前存在若干历史 untracked docs/reports，包括 parser review、V3.x 历史评测和 V4 baseline 本地 artifact。
- 上述既有 dirty worktree 内容未清理、未恢复、未纳入本任务，也未执行 `git add .`、commit 或 branch creation。

## 4. V4.5.1 Readiness

实际 stability artifact 记录：

- `verification_status=VERIFIED`；
- 4 representative cases，每条 3 runs；
- Prompt Evidence identity/order：4/4 exact match；
- raw answer：4/4 exact match；
- final answer：4/4 exact match；
- `stream=false`、`temperature=0.0`、`seed=42`；
- Ollama `0.33.2`、`qwen2.5:7b`、model digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`。

因此可以开展 fixed-environment controlled experiments。该结论只覆盖当前 runtime、Ollama version、model identity/digest、generation configuration 和 inference backend，不代表跨硬件、跨版本或跨 backend 的 universal determinism。

## 5. Human Failure Distribution

| 项目 | 结果 |
| --- | ---: |
| Human Full Pass | 7/12（58.33%） |
| Severe failure | 4/12（33.33%） |
| Unsupported claim | 4/12（33.33%） |
| Critical safety omission | 1/12（8.33%） |
| Primary GENERATION | 4 |
| Primary RETRIEVAL | 1 |
| Primary NONE | 7 |

高频标签：`GENERATION_GROUNDING_FAILURE=4`、`CONDITION_HANDLING_FAILURE=4`、`UNSUPPORTED_EXTRAPOLATION=4`、`CONTEXT_CONTAMINATION=3`、`COMPLETENESS_FAILURE=3`。这些数字只能称为 12-case dev diagnostic set 的结果。

## 6. Case-by-Case Root Cause Analysis

### 6.1 `abs_fault_warning_answer_001`

- 观察失败：遗漏“立即在安全区域停车”，加入“制动性能可能受影响、谨慎驾驶”等当前 Prompt Evidence 不能直接支持的表述；存在唯一 critical safety omission。
- Exact Prompt Evidence：ABS 功能说明、故障警告灯、正常振动说明和通用故障处理；不含专用停车指令。
- 冻结 human attribution：Primary=GENERATION。该裁决保持不变。
- 事后根因判断：canonical gold chunk `7ec78836-...` 未出现在冻结 no-rerank top-5，也未进入 Prompt。现有 artifact 未保存 dense/BM25 candidate、fusion 后完整候选、filter/dedup、metadata selection 和 budget 的逐阶段 trace，故专用 Evidence 在哪个子阶段丢失为 `UNKNOWN / INSUFFICIENT TRACE`。
- Primary root-cause layer：`UNKNOWN`（retrieval/ranking/context availability 子阶段不可判定）。
- Secondary：`GENERATION`，因为模型仍生成了无直接依据的制动性能和谨慎驾驶断言。
- 置信度：MEDIUM。

### 6.2 `epb_enable_release_answer_001`

- 观察失败：正常启用步骤缺失；模型把释放操作和紧急制动污染成“启用”方法，并产生方向/条件错误。
- Exact Prompt Evidence：包含正常释放、D/R 挡加速释放、手动紧急制动、概念说明和溜车警告；不含正常启用 chunk `a485ba75-...`。
- 冻结 no-rerank top-5：正常释放 gold 在 rank 2，正常启用 gold 不在 top-5。冻结 rerank artifact 中正常启用出现在 rank 3，证明 chunk 存在且曾进入 rerank 候选链路，但不能反推 V4.4 每个中间阶段。
- Primary：`RANKING` / final context availability（MEDIUM confidence）。
- Secondary：`GENERATION`，因为模型在 Evidence 不足时未拒绝或限定回答，反而将 emergency Evidence 泛化。
- 限制：冻结 retrieval Hit@K 使用 ANY_OF，命中“释放”不能证明“启用+释放”互补 Evidence 都可用。本阶段不新增 GoldEvidenceCoverage 指标。

### 6.3 `epb_poweroff_release_answer_001`

- 观察失败：第一条合法路径遗漏“先关闭 EPB AUTO”；第二条路径与溜车警告保留。
- Exact Prompt Evidence：E1 完整包含两条路径及第一条的前置条件。
- Primary：`GENERATION`。
- Secondary：`PROMPT_POLICY` 候选，因为当前生成合同没有把前置条件保持提升为明确、可验证的不变量；这不等于已经证明 Prompt 是唯一根因。
- 置信度：HIGH。

### 6.4 `remote_key_start_answer_001`

- 观察失败：把“钥匙电量低且系统无法检测到钥匙”时的杯托放置步骤提升为普通启动第一步。
- Exact Prompt Evidence：E1 明确标注紧急条件，E2 给出普通启动步骤；两者均模型可见。
- Primary：`GENERATION`。
- Secondary：`PROMPT_POLICY` 候选；E1 排在 E2 前可能增加误用风险，但正确 general Evidence 已存在，不能把错误归为 retrieval miss。
- 置信度：HIGH。

### 6.5 `epb_auto_subsection_answer_001`

- 观察失败：核心“静止并熄火后自动启用 EPB”正确，但继续引入 P 挡、手动 EPB、START/STOP 和释放态警告，扩大了问题范围。
- Exact Prompt Evidence：E1 已独立直接回答；E2-E5 提供其他 EPB/熄火程序和条件。
- Primary：`GENERATION`。
- Secondary：`PROMPT_POLICY`（answer scope）；context contamination 是促成条件，不等于必须先改 selector。
- 置信度：HIGH。

## 7. Retrieval -> Prompt Evidence Trace Analysis

| Case | Frozen retrieval observation | Exact Prompt observation | 可定位结论 | Trace gap |
| --- | --- | --- | --- | --- |
| ABS fault | no-rerank top-5 无专用停车 gold；rerank top-1 有该 gold | Prompt 无专用停车 gold | Evidence availability failure 发生在生成前 | 无逐阶段 candidate/filter/selection/budget trace，具体子阶段未知 |
| EPB enable/release | no-rerank top-5 仅有 release gold；rerank top-3 同时有 enable/release | Prompt 无 enable gold | no-rerank 最终上下文缺互补 Evidence | V4.4 未保存完整候选和 selection 决策，ranking 与 selection 的精确边界不足 |
| EPB poweroff release | 直接完整 Evidence 可见 | E1 完整进入 Prompt | 非 retrieval/context availability failure | 无关键 gap |
| Remote key start | no-rerank top-3 有 normal gold；emergency rank 1 | normal 与 emergency 均可见 | Evidence 充分，错误发生在 evidence use | 无关键 gap |
| EPB AUTO | 直接 core Evidence 可见 | E1 已完整回答 | Evidence 充分，错误是 scope expansion | 无关键 gap |

V4.4 artifact 保存了 exact Prompt Evidence，但没有保存每个 case 的全量 candidate 和逐阶段去留理由。因此本报告不会把“未进入 Prompt”自动命名为 retrieval、ranking、selection 或 budget 的某一个确定失败。

## 8. Condition Preservation Analysis

建议建立通用 Condition Preservation Principle：当 Evidence 中的操作结论受 prerequisite、车辆/功能状态、normal/emergency、AUTO/manual、点火、挡位、制动、故障或环境条件约束时，回答不得移除该条件或把特殊条件提升为默认流程。

直接目标：

- `remote_key_start_answer_001`：杯托步骤必须保留“钥匙电量低且无法识别”条件。
- `epb_poweroff_release_answer_001`：第一条路径必须保留“关闭 EPB AUTO”前置条件。

潜在收益：减少去条件化、特殊规则泛化和 unsupported extrapolation。主要风险是机械复述、答案变长，以及对无条件事实添加不存在的条件。实验必须检查条件只在 Evidence 明确存在时保留，不要求模型为每句话重复全部背景。

## 9. Answer Scope Analysis

建议的通用原则是：Prompt Evidence 是可用证据集合，不是必须全部写入答案的清单。回答应只使用直接回答当前 question scope 所必要的 Evidence；仅当问题明确要求“所有、哪些、分别、完整步骤”等 exhaustive information 时，才系统覆盖全部相关条目。

直接目标：

- `epb_auto_subsection_answer_001`：core answer 后停止，不引入其他熄火/手动/释放程序。
- `remote_key_start_answer_001`：普通流程与 emergency 条件分层，不把全部相关 Evidence 串成单一路径。

回归风险：过度压缩会破坏 `remote_start_blocked_answer_001` 的 canonical 8 conditions 和 `charging_led_list_answer_001` 的完整颜色列表，也可能使安全 warning 遗漏。因此禁止使用“总是简短”作为干预。

## 10. Context Selection Analysis

本轮不建议立即修改 context selector：

1. ABS 和 EPB 启用/释放确有 evidence availability 问题，但现有 artifact 不能精确区分 candidate retrieval、fusion ranking、filter/dedup、metadata selection 和 budget。
2. 三条 generation failures 的正确 Evidence 已完整进入 Prompt，先验证 evidence-use policy 更容易保持单变量归因。
3. 同时改 Prompt 与 selector 会无法判断收益来自哪一层。

后续若处理 ABS/EPB availability，应先在独立诊断实验中保存逐阶段 chunk IDs、rank、selection reason 和 budget exclusion reason，再决定是 ranking 还是 context selection intervention。不得用 case-specific selector bonus 修复。

## 11. Failure -> Intervention Matrix

| Case ID | Observed Failure | Prompt Evidence Situation | Root Cause Hypothesis | Primary | Secondary | Candidate Intervention | Expected Benefit | Regression Risk | Guard Cases | Validation | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `abs_fault_warning_answer_001` | 安全指令遗漏 + 无依据扩写 | 专用停车 Evidence 缺失 | availability 子阶段未知；模型又未在不足时收敛 | UNKNOWN | GENERATION | 先补 trace；不纳入首个 Prompt treatment 的成功目标 | 可定位缺失层，避免误改 selector | 新 trace 增加 artifact 复杂度 | ABS explanation、hard negative | 逐阶段 identity trace + 人工审计 | MEDIUM |
| `epb_enable_release_answer_001` | 启用缺失、释放/紧急混用 | release 有，enable 无 | no-rerank ranking/final-context 缺互补证据 | RANKING | GENERATION | 独立 context availability 实验，晚于首个 generation experiment | 完整互补 Evidence | 扩大 context 污染 | EPB AUTO、EPB poweroff | fixed reference + trace + human rubric | MEDIUM |
| `epb_poweroff_release_answer_001` | 漏前置条件 | 完整 Evidence 可见 | prerequisite 未被保留 | GENERATION | PROMPT_POLICY | Condition Preservation | 提升 condition handling/correctness | 冗长、机械复述 | overspeed、pressure wash | exact output + human rubric | HIGH |
| `remote_key_start_answer_001` | emergency 步骤泛化为 normal | normal/emergency 均可见 | applicability condition 被移除 | GENERATION | PROMPT_POLICY | Condition Preservation | 防止 special-to-general promotion | 过度分支答案 | remote-start blocked、hard negative | exact output + human rubric | HIGH |
| `epb_auto_subsection_answer_001` | 正确后无必要扩写 | core E1 足够，其他 Evidence 干扰 | Evidence availability 被误当 mandatory use | GENERATION | PROMPT_POLICY | Answer Scope（第二实验） | 减少 contamination 和 procedural expansion | 列表完整性下降 | charging LED、remote-start blocked | human rubric + coverage guards | HIGH |

## 12. Regression Guard Matrix

| Guard Case | 必须保持的行为 | 主要防护风险 |
| --- | --- | --- |
| `pressure_wash_warning_answer_001` | 保留安全距离和禁止事项 | 条件/安全信息被压缩 |
| `overspeed_condition_answer_001` | 保留触发与解除条件 | 条件原则机械化或漏条件 |
| `remote_start_blocked_answer_001` | 完整覆盖 canonical 8 conditions | Answer Scope 过度缩短 exhaustive list |
| `abs_explanation_answer_001` | 准确说明 ABS 作用，不引入故障流程 | 主题污染 |
| `autohold_explanation_answer_001` | 保持短暂停车和释放关系 | 条件重述导致失真 |
| `charging_led_list_answer_001` | 完整枚举颜色/状态 | Answer Scope 破坏列表完整性 |
| `unsupported_voice_brake_calibration_answer_001` | 继续明确拒绝无依据组合 | 相关词拼接成伪答案 |

## 13. Intervention Priority

1. **Condition Preservation，优先级 P0**：两条高置信 generation failures 有完整 Prompt Evidence，变量清晰，回归护栏明确。
2. **Answer Scope，优先级 P1**：针对正确后扩写和 evidence contamination，但必须与 exhaustive-list 行为分开验证。
3. **Context availability trace，优先级 P1 diagnostic**：先补可诊断性，再决定 ranking/selection 实验；不与 Prompt experiment 同时进行。
4. **Rerank answer-level A/B，暂不执行**：V3.5 retrieval 指标收益不自动等于 answer-quality 收益，且历史 elapsed 不是 online latency benchmark。

## 14. V4.6-B Controlled Experiment Design

### 14.1 Fixed-generation controlled reference

在解释任何 treatment 前，先生成一个独立 reference artifact：当前稳定 production pipeline、当前 Prompt、hybrid、rerank=false、top_k=5、metadata selection=true、neighbor expansion=false、max_contexts=5、max_context_chars=6000、`qwen2.5:7b`、`temperature=0.0`、`seed=42`、`stream=false`。它不能覆盖 V4.4 historical baseline。

### 14.2 Treatment A: Condition Preservation only

- **Hypothesis**：明确要求保留 Evidence 的 applicability/prerequisite，可改善条件遗漏和 special-to-general promotion，而不破坏 exhaustive-list、hard-negative 和安全回答。
- **Independent Variable**：仅增加一条通用 Condition Preservation generation contract；具体文本在 V4.6-B 分支评审。
- **Frozen Variables**：dataset、semantics v4.3、retrieval、RRF、rerank=false、selection、budget、answer model、temperature、seed、stream、sanitizer、evaluator。
- **Target Cases**：`epb_poweroff_release_answer_001`、`remote_key_start_answer_001`。`epb_auto_subsection_answer_001` 只观察，不作为该实验必须改善项。
- **Regression Guards**：第 12 节全部 7 条。
- **Success Criteria**：两个 target 的 condition handling 均至少提升 1 分；不再出现对应 prerequisite omission/special-condition promotion；target 不新增 unsupported claim；7 个 guards 不丢失 Human Full Pass；hard negative 保持拒答；critical safety omission 不增加；internal reference leak 与 deterministic sanitizer checks 保持通过。
- **Reject Criteria**：任一 guard 从 full pass 退化、出现新 unsupported claim/critical safety omission、exhaustive list 明显漏项，或两个 target 均无可复核改善。
- **INCONCLUSIVE**：只改善一个 target 且另一条无变化，但无 regression；或人工评分分歧无法消解。此时不 merge。
- **Required Artifact**：reference/treatment raw+final answer、exact Prompt Evidence、配置与 runtime identity、自动 checks、逐 case human rubric、comparison report。
- **Branch Name**：`exp/v4.6-condition-preservation`。
- **Merge Criteria**：满足 Success Criteria、实现保持单一通用规则且可维护，经人工 review 后才作为 merge candidate。

### 14.3 Treatment B: Answer Scope only（后续候选）

在 Treatment A 完成并作出 ACCEPT/REJECT/INCONCLUSIVE 决策后，才单独设计。不得与 Condition Preservation 合并为第一轮 treatment。目标 case 是 `epb_auto_subsection_answer_001`，核心 guards 是两条 exhaustive-list cases。

## 15. Branch / Merge Strategy

V4.6-A 不创建 branch。V4.6-B 真正开始实现时，从稳定 `main` 创建 `exp/v4.6-condition-preservation`。分支只包含该单变量实现、tests 和实验 artifact；不夹带当前工作区历史修改。

决策规则：

- `ACCEPT`：达到预设 success criteria，进入 merge candidate；
- `REJECT`：有明确无收益或 regression，不合并实现；
- `INCONCLUSIVE`：证据不足，不合并并继续设计；
- 三种结果都保留 experiment report。

## 16. Deferred Work

- V4.7：Answer Model capability benchmark；本轮不更换 `qwen2.5:7b`。
- V4.8：Embedding / Retrieval Model benchmark；本轮不更换 embedding 或重开 retrieval freeze。
- V4.9：Query Transformation，包括 rewrite/multi-query/HyDE；本轮不实现。
- ABS/EPB complementary Evidence 的逐阶段 availability trace：作为独立 diagnostic 工作，不在首个 Prompt treatment 中混改。
- rerank answer-level A/B、正式 latency p50/p95：需另立实验，不把 V3.5 retrieval elapsed 当在线结论。

## 17. Known Limitations

- 只有 12 条 answer dev diagnostic cases，不能代表 production、跨车型或跨手册质量。
- V4.4 使用 inherited generation defaults；它只能作为 historical baseline。
- V4.5.1 stability verification 覆盖 4 cases x 3 runs，只证明当前固定环境下的 exact-output stability。
- V4.4 未保存完整逐阶段 retrieval/context decision trace，ABS 和 EPB enable 的精确丢失层无法判定。
- ANY_OF retrieval semantics 不衡量互补 Evidence 完整覆盖；本轮不修改冻结 evaluator。
- 自动 evaluator 存在 4 条 proxy false negatives，V4.6 实验必须保留人工 rubric。

## 18. Global Sync Audit

| 信息面 | 判断 | 动作 |
| --- | --- | --- |
| `README.md` | UPDATE_REQUIRED | 最小同步 V4.5.1、V4.6-A、controlled experiment 与 V4.7-V4.9 roadmap |
| `AGENTS.md` | UPDATE_REQUIRED | 增加长期 experiment branch/merge policy、Global Sync Audit 和当前阶段边界 |
| `docs/evaluation.md` | UPDATE_REQUIRED | 修正“Answer Evaluation 是后续阶段”的过时表述；不改变 retrieval methodology |
| V4.4/V4.5 frozen artifacts | NO_UPDATE_NEEDED | 保留历史 generation defaults 和人工裁决，不回写 |
| V4.5.1 stability artifacts | NO_UPDATE_NEEDED | 三份 artifact 已一致且 VERIFIED |
| `.env.example` / config docs | NO_UPDATE_NEEDED | 本轮没有配置变化 |
| CLI/help text | NO_UPDATE_NEEDED | 本轮没有行为或命令变化 |
| tests / code comments | NO_UPDATE_NEEDED | 本轮没有 Python 或 production behavior 变化 |

## 19. V4.6-B Readiness Decision

- `ROOT_CAUSE_MAPPING_COMPLETE = YES`
- `SYSTEMIC_INTERVENTIONS_IDENTIFIED = YES`
- `CASE_SPECIFIC_HACKS_REQUIRED = NO`
- `CONTROLLED_REFERENCE_REQUIRED_BEFORE_V4_6_B = YES`
- `READY_FOR_V4_6_B_CONTROLLED_IMPLEMENTATION = YES`

最后两个标志不冲突：可以进入独立实验分支实施单变量 treatment，但在解释 treatment 结果之前，必须先用 V4.5.1 固定 generation configuration 生成并冻结 controlled reference。ABS 与 EPB enable 的 trace gap 不阻塞 Condition Preservation 实验，因为它们不是该 treatment 的主要 success targets；它们也不得被伪装成已解决。
