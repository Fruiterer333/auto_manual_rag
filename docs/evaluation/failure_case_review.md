# Failure Case Review

## 1. 背景

本文基于 V3.2 阶段清洗后的 69 条 text-only dev cases，对比以下两条链路：

- baseline：hybrid retrieval，不启用 rerank；
- experiment：hybrid retrieval + `BAAI/bge-reranker-base`。

rerank 在当前 dev set 上显著提升了 top-1 evidence ranking：

- `evidence_hit@1`：`0.7681 -> 0.9130`；
- `MRR`：`0.8792 -> 0.9541`；
- `evidence_hit@3`：保持 `1.0000`；
- `evidence_hit@5`：保持 `1.0000`。

本文不重复完整指标报告，而是分析 rerank 后仍存在的 non-top1 cases、唯一 regression，以及这些现象背后的工程原因。目标不是立即新增规则，而是为后续 chunking、metadata、rerank 参数实验和模块瘦身提供依据。

当前 eval set 是单一手册的 development evaluation set，不是 final benchmark。当前系统也是 text-only RAG，不处理依赖图标、按钮示意图、编号图例或视觉版面的 manual QA。

## 2. 数据来源

- dataset：`data/eval/manual_eval_set.jsonl`
- comparison report：`reports/evaluation/v3_2_rerank_comparison.md`
- baseline report：`reports/evaluation/v3_2_hybrid_no_rerank.md`
- rerank report：`reports/evaluation/v3_2_hybrid_rerank.md`
- case count：`69`
- retrieval mode：`hybrid`
- reranker：`BAAI/bge-reranker-base`
- `rerank_top_n`：`10`
- `rerank_output_top_k`：`5`
- `top_k`：`5`

现有单模式报告使用 coarse failure criteria，因此在 `evidence_hit@5=1.0000` 时显示没有 failure cases。本文进一步检查 top-1 排序、chunk 内容和 metadata，不将“进入 top-5”误解为“问题已经解决”。

## 3. 总体观察

- rerank 主要改善 ordering，不是扩大 recall。
- 当前所有 eval cases 的正确 evidence 都进入 top-5，因此 `retrieval_recall_failure` 不是主要瓶颈。
- rerank 后仍有 1 个 regressed case 和 4 个 unchanged non-top1 cases。
- 剩余问题集中在相似文本排序、chunk boundary、section metadata 和 multi-evidence list coverage。
- 个别 case 还暴露 eval annotation 需要复核的问题。标注问题不应通过 retrieval 或 rerank 补丁修复。
- 不应根据单个 case 直接新增 BM25 penalty、metadata bonus、rerank 特例或 prompt 规则。

## 4. Failure Taxonomy

| failure_type | 定义 | 后续处理建议 |
| --- | --- | --- |
| `retrieval_recall_failure` | 正确 evidence 没有进入 top-k。 | 先检查索引、retrieval 和过滤链路。当前 V3.2 中预期没有该类。 |
| `rerank_ordering_failure` | 正确 evidence 已在 top-k，但 rerank 没有排到 top-1，或使排名下降。 | 通过 case review 和参数对照观察，不为单个 case 添加特例。 |
| `chunk_boundary_issue` | 一个 chunk 混入多个主题，或操作步骤、长列表被拆分。 | 后续检查 parser、splitter 和 chunk inspection 结果。 |
| `section_metadata_issue` | section 缺失、错位或继承自相邻章节。 | 后续改进 heading 继承和 metadata 质量，不用 prompt 或 rerank 掩盖。 |
| `multi_evidence_list_issue` | 问题需要多条 evidence；单个 top-1 chunk 不足以覆盖完整答案。 | 后续增加 answer-level coverage evaluation，再评估上下文组织策略。 |
| `query_intent_ambiguity` | 问题表达宽泛，或与相似功能、相似操作存在语义重叠。 | 先分析问题类型分布，不立即引入 query rewrite。 |
| `visual_dependent_excluded` | 核心答案依赖图标、按钮示意图、编号图例或视觉版面。 | 从 text-only 主评测中删除、改写或单独标注为未来多模态扩展。 |
| `eval_annotation_issue` | question、expected pages、evidence 或 `answer_must_cover` 存在不一致。 | 复核标注，不通过系统规则迎合错误或不完整标注。 |
| `acceptable_limitation` | case 仍非 top-1，但正确 evidence 已靠前，top-1 也是同主题有效内容，暂不需要改系统。 | 记录并观察，不优先处理。 |

## 5. Regressed Cases

### `brake_warning_lights_001`

| item | value |
| --- | --- |
| question | 制动系统红色和黄色警告灯分别在什么情况下点亮？ |
| baseline evidence rank | `2` |
| rerank evidence rank | `3` |
| baseline top-1 | page `73`, section `N/A` |
| rerank top-1 | page `76`, section `N/A` |
| expected evidence | page `155`, section `制动系统` |
| evidence summary | 制动液液位低、传感器故障或电子制动力分配功能故障时点亮红色警告灯；制动系统故障时点亮黄色警告灯。 |
| top-5 regression | 否，正确 evidence 仍在 top-5 内。 |

#### 现象

baseline 将 page `73` 的警告灯总览排在 top-1，将 page `155` 的 `制动系统` evidence 排在 rank `2`。rerank 后 page `76` 的警告灯列表上升到 top-1，page `73` 排在 rank `2`，page `155` 的标注 evidence 降到 rank `3`。

page `73` 的文本已经包含与问题直接相关的红色和黄色制动系统警告灯说明，只是它不是当前 eval case 标注的 expected evidence。page `76` 则是更泛的警告灯列表，包含多种系统状态。

#### 判断

- 主要类型：`rerank_ordering_failure`
- 同时涉及：`section_metadata_issue`
- 需要复核：`eval_annotation_issue`

这是轻微 regression，不是 recall failure。正确 evidence 仍在 top-5 内，而且 baseline top-1 的 page `73` 可能是合理 alternate evidence。当前标注只接受 page `155`，可能低估了警告灯总览的有效性。

#### 建议

- 先人工复核 page `73` 是否应作为可接受 evidence 或 alternate evidence。
- 记录 rerank 对警告灯列表类 chunk 的排序偏好。
- 不为该 case 增加警告灯专用 rerank rule、BM25 penalty 或 metadata bonus。


## 6. Unchanged Non-Top1 Cases

### `epb_enable_release_001`

| item | value |
| --- | --- |
| question | 电子驻车制动如何启用和释放？ |
| baseline evidence rank | `2` |
| rerank evidence rank | `2` |
| baseline top-1 | page `159`, section `手动紧急制动` |
| rerank top-1 | page `159`, section `手动紧急制动` |
| expected evidence | page `157` 的 EPB 启用步骤，以及 page `158` 的 EPB 释放步骤 |

#### 现象

top-1 是手动紧急制动：行驶中拉住电子驻车制动器开关启用紧急制动，松开开关后解除紧急制动。它与常规 EPB 启用和释放共享“电子驻车制动”“启用”“释放”和“开关”等词。

rerank 后 rank `2` 是释放 EPB 的说明 chunk，但该 chunk 还混入 EPB AUTO 设置内容。完整回答需要 page `157` 和 page `158` 的多条 evidence。

#### 判断

- 主要类型：`query_intent_ambiguity`
- 同时涉及：`chunk_boundary_issue`
- 次要类型：`multi_evidence_list_issue`

#### 是否需要马上修改系统

不需要。正确 evidence 已进入 top-5，且问题同时询问启用和释放，本身需要多条 evidence。手动紧急制动与常规 EPB 操作的语义高度接近，不应通过 query-specific 规则区分。

#### 建议处理

- 检查 page `157` 至 page `159` 的 chunk boundary 是否将常规 EPB、EPB AUTO 和手动紧急制动拆分清楚。
- 后续 answer-level coverage evaluation 应验证最终回答是否同时覆盖“静止时拉起”和“踩下制动踏板后按下”。
- 暂不引入 query rewrite。

### `front_hood_close_warning_001`

| item | value |
| --- | --- |
| question | 关闭前机舱盖前需要确认什么？ |
| baseline evidence rank | `2` |
| rerank evidence rank | `2` |
| baseline top-1 | page `308`, section `N/A` |
| rerank top-1 | page `308`, section `N/A` |
| expected evidence | page `308`：关闭区域无障碍物，发动机舱内未遗留手套、抹布或其他易燃物。 |

#### 现象

top-1 和标注 evidence 都位于 page `308`，但分布在相邻 chunks。top-1 是关闭机舱盖的操作步骤，并包含“检查确保其已完全关闭”；rank `2` 是关闭前的安全警告。两个 chunks 的 section 都是 `N/A`。

当前 `answer_must_cover` 还要求覆盖“驾车前确认完全关闭锁止”，但现有 evidence quote 只标注了关闭区域和易燃物检查。这个覆盖点虽然出现在相邻 chunk 中，但没有纳入当前 evidence quote。

#### 判断

- 主要类型：`section_metadata_issue`
- 同时涉及：`chunk_boundary_issue`
- 需要复核：`eval_annotation_issue`
- 可接受部分：`acceptable_limitation`

#### 是否需要马上修改系统

不需要。top-1 是同页同主题的有效操作步骤，不是无关内容。当前主要问题是 metadata 缺失、警告与操作步骤被拆入相邻 chunks，以及标注 evidence 未完整覆盖 `answer_must_cover`。

#### 建议处理

- 优先复核 eval annotation，使 evidence 与 `answer_must_cover` 对齐。
- 后续检查前机舱盖 heading 继承和 warning block 边界。
- 不通过 rerank 特例或 prompt 补丁解决。

### `hazard_light_emergency_001`

| item | value |
| --- | --- |
| question | 什么情况下应启用危险警告灯？ |
| baseline evidence rank | `2` |
| rerank evidence rank | `2` |
| baseline top-1 | page `89`, section `使用超车灯` |
| rerank top-1 | page `89`, section `使用超车灯` |
| expected evidence | page `89`：交通事故或其他紧急情况下，按下危险警告灯按键启用危险警告灯。 |

#### 现象

top-1 是“发生碰撞情况下，危险警告灯也将自动点亮”的说明。rank `2` 才是手动启用危险警告灯的标注 evidence。

正确 evidence 所在 chunk 还包含超车灯说明和“使用危险警告灯”标题，但 section metadata 仍继承为 `使用超车灯`。这说明标题断块或 section 继承存在错位。

#### 判断

- 主要类型：`chunk_boundary_issue`
- 同时涉及：`section_metadata_issue`
- 次要类型：`query_intent_ambiguity`
- 可接受部分：`acceptable_limitation`

#### 是否需要马上修改系统

不需要。top-1 与问题高度相关，只是回答“碰撞后自动点亮”，而标注 evidence 回答“何时应手动启用”。这是相邻概念之间的排序差异，不应通过危险警告灯专用规则修复。

#### 建议处理

- 后续检查 page `89` 的 heading 断块和 section metadata 继承。
- 在 answer-level evaluation 中区分自动点亮说明与手动启用场景。
- 暂不新增 query rewrite 或 metadata bonus。

### `pressure_wash_warning_001`

| item | value |
| --- | --- |
| question | 使用高压水枪清洗车辆时有哪些注意事项？ |
| baseline evidence rank | `2` |
| rerank evidence rank | `2` |
| baseline top-1 | page `317`, section `高压冲洗` |
| rerank top-1 | page `317`, section `高压冲洗` |
| expected evidence | page `317`：外部开闭件、底部接插件、传感器距离、喷嘴距离和发动机舱冲洗限制。 |

#### 现象

top-1 是同一 section 下的高压水枪通用提醒，包括设备操作说明、工作压力、喷水距离和软材料保护。rank `2` 是较长的安全警告列表，覆盖当前 case 的主要 `answer_must_cover`。

top-1 不是无关内容，但不足以完整回答宽泛列表问题。单个 top-1 排名无法表达“多个同主题 chunks 应共同进入最终上下文”的需求。

#### 判断

- 主要类型：`multi_evidence_list_issue`
- 同时涉及：`acceptable_limitation`

#### 是否需要马上修改系统

不需要立即调整 retrieval 或 rerank。该 case 更适合用 answer-level coverage 和最终 context coverage 评估，而不是只看 top-1 evidence。

#### 建议处理

- 后续增加 answer-level coverage evaluation，检查长列表是否被完整覆盖。
- 检查最终 context 是否同时保留 top-1 通用提醒和 rank `2` 安全列表。
- 不用 prompt 要求模型补充未进入上下文的条目。

## 7. Section Metadata Issues

本轮 failure review 中出现以下 section metadata 问题：

- `brake_warning_lights_001` 的警告灯总览 chunks 为 section `N/A`；
- `front_hood_close_warning_001` 的关闭步骤和安全警告 chunks 均为 section `N/A`；
- `hazard_light_emergency_001` 的危险警告灯内容仍继承 section `使用超车灯`。

section metadata 问题会影响 `section_hit` 和人工解释，但不必然代表 retrieval failure。如果 page、chunk_id 和 quote 正确，应结合 evidence 内容判断。

后续应通过 parser、splitter、heading 继承和 chunk inspection 改善 metadata 质量，不应通过 rerank、prompt 或 query-specific rule 掩盖问题。

## 8. Chunk Boundary and Multi-topic Issues

当前可见的 chunk boundary 和多主题问题：

- `epb_enable_release_001`：常规 EPB 释放说明与 EPB AUTO 设置混在一个 chunk 中，手动紧急制动又与常规 EPB 操作高度相似。
- `hazard_light_emergency_001`：超车灯和危险警告灯内容落在同一 chunk 或相邻 block 中，section 仍为 `使用超车灯`。
- `front_hood_close_warning_001`：关闭步骤和关闭前安全警告被拆分为相邻 chunks，section metadata 缺失。
- `pressure_wash_warning_001`：通用提醒与较长安全列表分布在同一 section 的不同 chunks 中，top-1 排名不足以表示答案完整性。

这类问题更适合在后续 chunking / metadata review 中处理，不适合在 V3.3 直接调整检索规则。

## 9. Rerank Limitations

- cross-encoder rerank 对 top-1 ordering 有明显帮助，但只能重排已有候选。
- rerank 不能修复 chunk boundary、metadata 错位、标注不一致或 visual-dependent 问题。
- rerank 可能在警告灯、相似安全类文本中出现轻微 regression。
- rerank 带来约 `1.81x` latency cost。
- 当前保持 `ENABLE_RERANK=false` 是合理的。rerank 应继续作为 optional enhancement，用于评测分析和可选高精度模式。

## 10. 不建议立即做的事情

- 不建议马上引入 query rewrite。
- 不建议为单个 case 添加 BM25、metadata 或 rerank 特例。
- 不建议默认开启 rerank。
- 不建议继续扩大 eval set 来掩盖 failure。
- 不建议用 prompt 要求模型补齐 retrieval 没有提供的内容。
- 不建议把 visual-dependent 问题重新加入 text-only dev set。

## 11. 后续优先级

### P0：接受并记录

- 记录 `brake_warning_lights_001` 的轻微 regression。正确 evidence 仍在 top-5，先复核 alternate evidence，不立即调规则。
- 确认 `parking_emergency_brake_fault_001` 的 expected page 为 `73`。该 case 已由 rerank 从 rank `2` 提升到 rank `1`，不是异常 case。

### P1：metadata / chunk boundary review

- 检查 section `N/A`、section 错位和同 chunk 多主题问题。
- 优先关注 `hazard_light_emergency_001`、`front_hood_close_warning_001` 和 `epb_enable_release_001`。
- 同时复核 `front_hood_close_warning_001` 的 evidence 与 `answer_must_cover` 是否完整对齐。

### P2：multi-evidence / long-list handling

- 检查 `pressure_wash_warning_001` 这类长列表安全问题。
- 后续增加 answer-level coverage evaluation，避免只用 top-1 rank 判断答案完整性。

### P3：rerank 参数实验

- 对比 `rerank_top_n=10` 与 `rerank_top_n=20`。
- 可选对比 `BAAI/bge-reranker-base` 与 `BAAI/bge-reranker-v2-m3`。
- 参数实验必须在 failure review 后进行，不提前调参。

### P4：query rewrite

- 暂不做。
- 只有当 failure review 证明大量失败来自 query intent 或用户表达问题时，再作为独立实验引入。

## 12. 结论

- rerank 在当前 69 条 text-only dev set 上有效。
- 当前主要剩余问题不是 top-5 recall，而是 top-1 ordering、metadata、chunk boundary 和 multi-evidence coverage。
- 下一步应优先做 chunk / section metadata review，并在后续设计 answer-level coverage evaluation。不应继续增加规则或立即引入 query rewrite。
- 当前 eval set 仍是 dev set，不是 final benchmark。
- 当前系统仍是 text-only RAG，不处理 visual-dependent manual QA。
