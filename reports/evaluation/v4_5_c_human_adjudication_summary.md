# V4.5-C 人工裁决汇总与失败分类报告

## 1. 范围与冻结实验身份

本报告汇总 V4.5-B 的最终人工裁决；它是对冻结 V4.4 基线的派生审计产物，不修改原始答案、检索行为、V4.3 评测语义或 answer-eval contract。

- 源基线：`reports/evaluation/v4_answer_baseline_hybrid_no_rerank_20260902_200054.json`
- 源基线生成时间：2026-09-02T20:03:02
- 人工裁决版本：`v4.5-b-final`
- 评测语义版本：`v4.3`
- case 数量：12（11 条正例，1 条 hard-negative）
- 检索配置：hybrid；rerank=false；top_k=5
- Context selection：true；neighbor expansion=false
- Context budget：max_contexts=5；max_context_chars=6000
- 模型：`qwen2.5:7b`；Ollama=0.33.2；digest=`845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`
- 生成参数：stream=false；temperature/seed/options 均未显式设置，因此严格可复现性仍为 **NO**。

## 2. 人工裁决方法

人工分数是本阶段唯一的 answer-quality 结论来源。自动检查、术语覆盖和结构命中只保留为诊断字段，不能覆盖人工裁决。Groundedness 审核仅使用模型实际可见的`prompt_evidence`；未进入 prompt 的 citation、索引内容或外部知识均不作为证据。

## 3. 12 条 Case 人工裁决汇总

| case_id | 五维评分 G/C/Co/Ch/S | unsupported | critical safety omission | 主要层 | 失败标签 | 评估器诊断 | 裁决摘要 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `epb_enable_release_answer_001` | 0/0/0/0/0 | true | false | RETRIEVAL | RETRIEVAL_FAILURE、CONTEXT_CONTAMINATION、GENERATION_GROUNDING_FAILURE、CONDITION_HANDLING_FAILURE、COMPLETENESS_FAILURE、UNSUPPORTED_EXTRAPOLATION | 无 | 正常启用 EPB 的直接 Evidence 未进入 prompt；现有上下文只覆盖部分互补的释放 Evidence，回答又混入紧急制动和不适用的释放条件。 |
| `remote_key_start_answer_001` | 1/0/2/0/2 | true | false | GENERATION | CONTEXT_CONTAMINATION、GENERATION_GROUNDING_FAILURE、CONDITION_HANDLING_FAILURE、UNSUPPORTED_EXTRAPOLATION | 无 | 普通遥控钥匙启动 Evidence 已存在，但回答把仅在钥匙电量低且未被检测到时适用的前杯托紧急启动步骤提升为无条件常规步骤。 |
| `pressure_wash_warning_answer_001` | 2/2/2/2/2 | false | false | NONE | 无 | EVALUATOR_PROXY_FALSE_NEGATIVE | 高压冲洗的安全距离和禁止事项均由模型可见 Evidence 直接支持；结构代理 miss 不构成回答失败。 |
| `abs_fault_warning_answer_001` | 1/0/0/1/0 | true | true | GENERATION | GENERATION_GROUNDING_FAILURE、COMPLETENESS_FAILURE、SAFETY_PRESERVATION_FAILURE、UNSUPPORTED_EXTRAPOLATION | 无 | 未要求立即在安全区域停车，且加入当前 Evidence 无法直接支持的谨慎驾驶和制动性能表述；联系领克中心的处理被保留。 |
| `abs_explanation_answer_001` | 2/2/2/2/2 | false | false | NONE | 无 | 无 | 防抱死系统的功能说明与模型可见 Evidence 一致。 |
| `autohold_explanation_answer_001` | 2/2/2/2/2 | false | false | NONE | 无 | 无 | Auto Hold 的短暂停车、制动踏板保持与加速释放关系均得到正确说明。 |
| `overspeed_condition_answer_001` | 2/2/2/2/2 | false | false | NONE | UNNECESSARY_PROCEDURAL_EXPANSION | EVALUATOR_PROXY_FALSE_NEGATIVE | 回答正确保留超速触发与低于阈值后解除的条件；“报警会自动解除”与合同术语不同，不应被当作完整性失败。 |
| `remote_start_blocked_answer_001` | 2/2/2/2/2 | false | false | NONE | 无 | EVALUATOR_PROXY_FALSE_NEGATIVE | 所有 canonical 的远程启动受阻条件均被正确覆盖；“发动机出现故障”等同义表述及结构代理差异不改变人工通过结论。 |
| `epb_auto_subsection_answer_001` | 1/1/2/1/2 | false | false | GENERATION | CONTEXT_CONTAMINATION、CONDITION_HANDLING_FAILURE、UNNECESSARY_PROCEDURAL_EXPANSION | 无 | 核心结论正确，但回答把其他 prompt Evidence 中的程序和条件扩展进来，造成不必要且有害的答案范围扩大。 |
| `epb_poweroff_release_answer_001` | 1/0/1/0/2 | true | false | GENERATION | GENERATION_GROUNDING_FAILURE、CONDITION_HANDLING_FAILURE、COMPLETENESS_FAILURE、UNSUPPORTED_EXTRAPOLATION | 无 | 第一条释放路径遗漏关闭 EPB AUTO 的必要条件；第二条路径仍有效且安全警告得到保留。 |
| `charging_led_list_answer_001` | 2/2/2/2/2 | false | false | NONE | 无 | EVALUATOR_PROXY_FALSE_NEGATIVE | 充电接口 LED 各颜色状态均由 canonical Prompt Evidence 覆盖；结构代理不一致不构成回答失败。 |
| `unsupported_voice_brake_calibration_answer_001` | 2/2/2/2/2 | false | false | NONE | 无 | 无 | hard-negative 的不足证据回答正确拒绝了在语音控制与制动系统 Evidence 之间进行无依据合成。 |

说明：G=groundedness，C=correctness，Co=completeness，Ch=condition handling，S=safety preservation；各项取值为 0/1/2。

## 4. 人工聚合指标

### 4.1 各维度分布与均值

| 维度 | 0 分 | 1 分 | 2 分 | 平均分 |
| --- | ---: | ---: | ---: | ---: |
| groundedness | 1 | 4 | 7 | 1.5000 |
| correctness | 4 | 1 | 7 | 1.2500 |
| completeness | 2 | 1 | 9 | 1.5833 |
| condition_handling | 3 | 2 | 7 | 1.3333 |
| safety_preservation | 2 | 0 | 10 | 1.6667 |

### 4.2 通过与严重失败

- Human Full Pass 定义：所有五个维度均为 2，且 unsupported_claim=false，且 critical_safety_omission=false。
- Human Full Pass：7/12 （58.33%）。
- Severe failure 定义：correctness=0 或 groundedness=0 或 safety_preservation=0，或 critical_safety_omission=true。
- Severe failure：4/12 （33.33%）。
- Unsupported claim：4/12 （33.33%）。
- Critical safety omission：1/12（8.33%）。

## 5. 失败分类与根因分析

### 5.1 主要失败层分布

| 层级 | case 数 |
| --- | ---: |
| RETRIEVAL | 1 |
| RANKING | 0 |
| CONTEXT_SELECTION | 0 |
| GENERATION | 4 |
| EVALUATOR | 0 |
| DATASET | 0 |
| NONE | 7 |
| UNCERTAIN | 0 |

### 5.2 失败标签频次

| 标签 | 次数 |
| --- | ---: |
| COMPLETENESS_FAILURE | 3 |
| CONDITION_HANDLING_FAILURE | 4 |
| CONTEXT_CONTAMINATION | 3 |
| GENERATION_GROUNDING_FAILURE | 4 |
| RETRIEVAL_FAILURE | 1 |
| SAFETY_PRESERVATION_FAILURE | 1 |
| UNNECESSARY_PROCEDURAL_EXPANSION | 2 |
| UNSUPPORTED_EXTRAPOLATION | 4 |

### 5.3 根因与症状必须分开理解

- **检索失败**：`epb_enable_release_answer_001` 的正常启用 Evidence 未进入模型上下文；这是 complementary-evidence 缺失，不可被 ANY_OF Hit@K 掩盖。
- **生成 grounding / 条件处理失败**：ABS 故障、遥控钥匙正常启动、EPB AUTO 与熄火后 EPB 释放等 case 的问题，主要表现为把通用或特殊条件错误推广为当前问题的确定步骤。
- **Context contamination** 是促成条件，不等同于回答层症状；真正的回答层问题仍可能是 `GENERATION_GROUNDING_FAILURE` 或`CONDITION_HANDLING_FAILURE`。
- **Unnecessary procedural expansion**：EPB AUTO 和超速 case 说明，即使核心结论正确，扩展无关程序也会降低答案边界清晰度；前者已影响人工评分，后者未降低五维评分。
- **Safety-preservation failure**：ABS 故障与 EPB 启用/释放 case 各存在安全要求的遗漏或弱化；ABS 为本次唯一的 critical safety omission。

## 6. 自动评估器分歧分析

以下 `EVALUATOR_PROXY_FALSE_NEGATIVE` 是评估器诊断，不是 answer failure，不会单独使 Human Full Pass 失败。

| 诊断 | 次数 | 相关 case | 说明 |
| --- | ---: | --- | --- |
| EVALUATOR_PROXY_FALSE_NEGATIVE | 4 | `pressure_wash_warning_answer_001`, `overspeed_condition_answer_001`, `remote_start_blocked_answer_001`, `charging_led_list_answer_001` | 词汇近义表达或 section/subsection 结构代理与模型可见的 canonical Evidence 不一致。 |

## 7. ABS 归因冲突的事后证据审计

人工裁决的 primary failure layer 保持为 **GENERATION**，评分与标签不作改写。但对冻结 V4.4 `prompt_evidence` 的复核显示：其中只有 ABS 功能说明、故障警告灯以及通用故障处理流程；并没有 contract 要求的“立即在安全区域停车”这一专属安全指令。因此，事后根因证据审计与人工 primary attribution 存在冲突。

该冲突被记录为 **需要显式协调**：人工 answer-quality 裁决仍然有效；但未来的根因归因不能把该 case 无条件视作纯 generation failure。

## 8. 多 Gold Evidence 的检索指标限制

冻结 V3.5 retrieval benchmark 对多个 gold evidence 使用 ANY_OF 语义：TopK 命中任意一个 gold，Hit@K 即成功。`epb_enable_release_answer_001` 显示，当答案合同要求互补 Evidence（例如“启用”与“释放”两个独立事实）时，`Hit@K = 1` 并不意味着完整答案所需的所有 Evidence 都已进入上下文。

这不是本阶段对冻结 retrieval evaluator 的修改。未来可候选引入：
`GoldEvidenceCoverage@K = |TopK ∩ GoldEvidence| / |GoldEvidence|`，并在数据集显式区分 `ANY_OF`（等价证据）与 `ALL_OF` / complementary groups（共同需要的证据）。

## 9. 已知限制

- 本报告仅覆盖 12 条 development answer-evaluation cases，不能代表生产质量、跨车型表现或用户在线体验。
- V4.4 使用 no-rerank 设置；本报告不比较 rerank on/off。
- 未设置 generation temperature、seed 和 options，严格 generation reproducibility 仍为 NO。
- elapsed time 是该次离线运行记录，不应解释为正式在线延迟指标。
- 自动评估器代理分歧只被标记，不在本阶段修改 evaluator、normalization 或 contract。

## 10. V4.5 结论与后续受控实验

V4.5 已将 V4.4 的自动检查与最终人工裁决分离、固化并汇总。当前最显著的answer-level 风险是：在多个 Evidence 同时存在时，模型对适用条件和答案范围的保持不足；同时存在一个需要与 retrieval evidence audit 协调的 ABS 安全 case。

后续实验应保持 V4.4 no-rerank 基线不变，并一次只改变一个变量。依据本次 taxonomy，优先候选为：

1. 对 no-rerank 与 rerank 做受控的 answer-level A/B，观察条件保持、上下文污染和安全遗漏是否变化。
2. 做 context-selection ablation，确认无关或特殊 Evidence 进入 prompt 是否是条件混合的必要前提。
3. 单独验证“条件/例外保持”与“避免无必要程序扩写”的 generation contract；不得在本报告基础上直接修改 prompt。
4. 将 complementary-evidence coverage 作为未来 retrieval/answer 联合评测的候选指标。
5. 对已标记的 evaluator proxy false negative 建立独立、受控的 evaluator 改进实验。

上述建议均为后续受控实验，不构成本阶段对 production RAG 的优化。
