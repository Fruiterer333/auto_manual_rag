# Evaluation Set Design

## 1. Purpose

`data/eval/manual_eval_set.jsonl` 是 development evaluation set，用于比较 retrieval、rerank、chunking 和 failure analysis 方案。它不是最终 benchmark，也不应被当作训练集或唯一优化目标。

本轮将评测集从 29 条扩展到 69 条。扩展目标是增加可诊断性和覆盖面，不是让某个检索方案的指标更好看。

> 当前状态：V3.5 已将该数据集校准并冻结为 69 records / 68 active / 1 excluded 的 chunk-level retrieval dev benchmark。本文保留 29 → 69 的设计历史；当前正式指标和 gold semantics 见 [`docs/evaluation.md`](../evaluation.md) 与 [`v3_5_retrieval_benchmark_summary.md`](../../reports/evaluation/v3_5_retrieval_benchmark_summary.md)。

## 2. Coverage

当前 dev set 覆盖以下问题类型：

- `procedure`：具体操作步骤，例如无钥匙进入、灯光、驻车、充电和维护操作。
- `warning_notice`：安全注意事项和禁止条件，例如涉水、充电、坡道驻车和高压冲洗。
- `parameter_query`：明确参数或限制，例如泊车雷达范围、座椅加热时长和空调风量等级。
- `maintenance_check`：检查和维护，例如安全带、胎压、制动片和低压蓄电池。
- `explanation`：功能说明，例如 ABS、Auto Hold、PEB、RPA 和预约充电。
- `alarm_handling`：报警状态或处理，例如胎压、ABS、制动系统、疲劳提醒和生命探测报警。
- `location_query`：位置查询，例如补胎套装、泊车传感器、保险丝盒和 VIN。
- hard negative cases：同主题相近章节之间的排序区分，例如 EPB 与手动紧急制动、PEB 说明与开关、APA 启用与泊入步骤、无钥匙解锁与闭锁、充电限值与预约充电。

## 3. Label Taxonomy

`category` 表示问题的主任务类型，统一使用以下 7 类：

| category | 定义 |
| --- | --- |
| `procedure` | 操作步骤类问题，询问如何启用、关闭、使用或设置某功能。 |
| `warning_notice` | 安全警告、禁止条件、风险提示或使用注意事项。 |
| `parameter_query` | 参数、限制、阈值、数值或规格类问题。 |
| `maintenance_check` | 检查、保养、维护或事件后检查类问题。 |
| `explanation` | 功能作用、状态含义或系统机制解释类问题。 |
| `alarm_handling` | 报警、故障提示、警告灯或异常状态处理类问题。 |
| `location_query` | 部件、标签、接口或编号的位置查询。 |

`intent_type` 表示用户意图的细粒度形式，统一使用以下 12 类：

| intent_type | 定义 |
| --- | --- |
| `specific_operation` | 明确询问具体操作步骤。 |
| `broad_usage_guidance` | 宽泛使用规范，通常需要多条 evidence。 |
| `safety_notice` | 安全注意事项或风险提示。 |
| `forbidden_condition` | 禁止行为、不可执行条件或不能做什么。 |
| `limit_parameter` | 数值限制、阈值、规格或可选范围。 |
| `location_query` | 纯位置查询。 |
| `location_and_operation` | 同时包含位置和操作。 |
| `location_and_parameter` | 同时包含位置和参数。 |
| `concept_explanation` | 功能作用、概念或系统机制说明。 |
| `state_explanation` | 状态、指示灯、模式差异或系统提示含义说明。 |
| `maintenance_guidance` | 检查、保养、维护或事件后检查。 |
| `alarm_handling` | 报警、故障或警告灯出现后的处理动作。 |

两类标签职责不同。例如：

- `category=warning_notice`、`intent_type=forbidden_condition`：安全警告类问题，具体询问禁止行为。
- `category=parameter_query`、`intent_type=location_and_parameter`：参数类问题，具体询问参数在哪里查看。
- `category=explanation`、`intent_type=state_explanation`：解释类问题，具体询问状态或指示灯含义。

## 4. Annotation Principles

- 每条 case 必须有来自当前 indexed chunk 的可验证 evidence。
- `evidence.quote` 使用真实 chunk 中的短句或短段，不凭常识编写。
- `expected_pages`、`expected_sections` 和 `must_contain_terms` 应尽量具体。
- section metadata 缺失或偏差时，在 `notes` 中说明，并结合 page、quote 和 terms 解读。
- hard negative case 用于测试相似章节排序，不用于写 query-specific 规则。
- 不添加需要图标识别、图片理解或外部知识才能回答的问题。
- 不为了指标好看而只添加极其简单的问题。
- 标签收敛只规范 `category` 和 `intent_type`，不修改 question 或 evidence，也不为提高指标而调整标注。

## 5. Current Scale

- case count：69
- split：当前统一为 `dev`
- source：单一本地汽车用户手册的 indexed chunks

后续应基于报告观察 category、intent、章节和失败类型分布，再补充 80 至 100 条样例，并逐步冻结独立 test set。

## 6. Visual-dependent Filtering

当前项目是 text-only RAG，不处理图片、图标、按钮示意图、编号图例和视觉版面。汽车用户手册中存在大量视觉说明，因此 dev set 需要明确区分文字检索问题和多模态理解问题。

- 核心答案依赖图示、按钮图标、编号图例或视觉位置的问题，不纳入当前 retrieval / rerank dev evaluation。
- 如果图示只是辅助信息，但文字 evidence 已经能独立回答，则可以保留。
- 如果问题可以改写为 text-only 可回答的问题，则优先改写。
- 被过滤的问题并非没有价值，而是留给未来 multimodal manual RAG 扩展。

This development evaluation set focuses on text-only retrievable evidence. Cases whose core answer depends on visual elements are either rewritten into text-only questions or excluded from the current retrieval evaluation. This avoids mixing multimodal understanding failures into text retrieval and rerank evaluation.

## 7. Limitations

- 当前仍是 dev set，不是最终 benchmark。
- 样本来自单一汽车用户手册，不能代表其他车型或品牌。
- 部分 chunk 的 section metadata 为空或存在解析偏差。
- 当前主要评估 retrieval 和 rerank，answer-level evaluation 尚未系统建设。
- 单个 case 的失败不能直接成为新增检索规则的依据。
