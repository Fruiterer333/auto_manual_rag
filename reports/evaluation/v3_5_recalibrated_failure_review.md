# V3.5 重校准检索失败复盘

## 执行摘要

本报告仅分析 V3.5 重校准后的检索评测结果，不修改生产检索、评测集、检索配置、parser、chunking、BM25、RRF 或 reranker。

- 活跃 case：**68**。另有 1 条因当前纯文本语料未表示表格数值而排除。
- Hybrid 无 rerank：`evidence_hit@1=0.6471`，`@3=0.9265`，`@5=0.9706`，`MRR=0.7848`，耗时 `31.2052s`。
- Hybrid + 当前 cross-encoder rerank baseline：`evidence_hit@1=0.8529`，`@3=0.9853`，`@5=1.0000`，`MRR=0.9203`，耗时 `37.4957s`。
- 无 rerank 的两个 Hit@5 失败 case，其当前 gold chunk 都存在于第一阶段候选集合中，但排名分别为第 6 和第 7。这属于第一阶段 RRF 排序和 chunk 特异性问题，并非语料中缺少证据。
- rerank 对现有排名第 2/3/4 的 gold evidence 最有帮助：共有 16 条 case 被提升到 top-1。同时存在 3 条 top-1 regression，均是同一技术领域内不同条件或不同作用域之间的竞争。

原始 JSON 评测产物只持久化了 rank、`chunk_id`、page、section、RRF score 和 evidence-hit 状态。以下五条深度分析中的候选 metadata、文本片段、dense/BM25 rank 和 rerank score，均通过相同 V3.5 配置进行只读重放得到。没有仅因检索排名靠前就反向定义 gold；gold 仍以重校准后的评测集为准。

## 失败数量

| 范围 | 数量 | Case ID |
|---|---:|---|
| 无 rerank，Hit@1 miss | 24 | `seatbelt_usage_001`、`seatbelt_fastening_001`、`tire_pressure_label_001`、`onboard_charging_steps_001`、`high_voltage_label_001`、`front_hood_open_001`、`front_hood_close_warning_001`、`wiper_caution_001`、`fuel_safety_001`、`epb_enable_release_001`、`keyless_entry_unlock_001`、`keyless_entry_lock_001`、`lock_auto_window_close_001`、`automatic_wiper_sensor_001`、`remote_key_start_001`、`abs_fault_handling_001`、`autohold_explanation_001`、`slope_parking_warning_001`、`parking_emergency_brake_fault_001`、`apa_exit_conditions_001`、`rpa_safety_001`、`fuse_box_location_001`、`vin_location_001`、`pressure_wash_warning_001` |
| 无 rerank，Hit@3 miss | 5 | `seatbelt_usage_001`、`onboard_charging_steps_001`、`fuel_safety_001`、`keyless_entry_lock_001`、`abs_fault_handling_001` |
| 无 rerank，Hit@5 miss | 2 | `onboard_charging_steps_001`、`abs_fault_handling_001` |
| rerank，Hit@1 miss | 10 | `seatbelt_usage_001`、`tire_pressure_alarm_001`、`onboard_charging_steps_001`、`high_voltage_label_001`、`wiper_caution_001`、`fuel_safety_001`、`epb_enable_release_001`、`brake_warning_lights_001`、`rpa_safety_001`、`pressure_wash_warning_001` |
| rerank，Hit@3 miss | 1 | `high_voltage_label_001` |
| rerank regression | 3 | `tire_pressure_alarm_001`、`high_voltage_label_001`、`brake_warning_lights_001` |
| rerank 改善 | 19 | 详见[rerank 改善的 19 条 case](#rerank-改善的-19-条-case) |

## 失败分类汇总

以下分类用于解释失败机制，不是新增 evaluator label。一个 case 可能同时存在多个影响因素；下表对 24 条无 rerank Hit@1 miss 使用单一主要分类。

| 主要分类 | Case 数量 | 含义 |
|---|---:|---|
| `SAME_SECTION_COMPETITION` | 12 | top-1 属于同一功能或系统，但回答的是另一个子问题、模式或条件。 |
| `PARTIAL_EVIDENCE_COMPETITION` | 4 | 候选包含请求事实的一部分，但不包含当前标注的直接证据。 |
| `QUERY_SCOPE_MISMATCH` | 2 | 宽泛请求或多部分请求被匹配到更窄的操作片段。 |
| `RRF_RANKING` | 2 | gold 在第一阶段候选集合中，但 dense/BM25 融合后未进入 top-5。 |
| `SEMANTIC_MISMATCH` | 3 | 结果属于不同功能或不同事实目标。 |
| `DUPLICATE_COMPETITION` | 1 | 其他部件或页面下的近似重复手册内容与当前 gold 竞争。 |

两个无 rerank Hit@5 miss 均没有被归类为 `TRUE_RECALL_FAILURE`：它们的精确 gold chunk 在 top-10 候选阶段都已存在。该分类结果不意味着现在应立即增加生产规则。

### 无 rerank Hit@1 miss 的主要分类

| 主要分类 | Case ID |
|---|---|
| `QUERY_SCOPE_MISMATCH` | `seatbelt_usage_001`、`epb_enable_release_001` |
| `SAME_SECTION_COMPETITION` | `seatbelt_fastening_001`、`tire_pressure_label_001`、`front_hood_close_warning_001`、`keyless_entry_unlock_001`、`keyless_entry_lock_001`、`lock_auto_window_close_001`、`automatic_wiper_sensor_001`、`remote_key_start_001`、`autohold_explanation_001`、`slope_parking_warning_001`、`parking_emergency_brake_fault_001`、`apa_exit_conditions_001` |
| `RRF_RANKING` | `onboard_charging_steps_001`、`abs_fault_handling_001` |
| `PARTIAL_EVIDENCE_COMPETITION` | `high_voltage_label_001`、`fuel_safety_001`、`rpa_safety_001`、`pressure_wash_warning_001` |
| `SEMANTIC_MISMATCH` | `front_hood_open_001`、`fuse_box_location_001`、`vin_location_001` |
| `DUPLICATE_COMPETITION` | `wiper_caution_001` |

## 无 rerank Hit@5 深度分析

### `onboard_charging_steps_001`

**问题：** 如何使用车载充电设备给车辆充电？
**主要分类：** `RRF_RANKING`，同时存在 `PARTIAL_EVIDENCE_COMPETITION` 和 `METADATA_OR_BOUNDARY_EFFECT`。

**当前 gold evidence**

- `chunk_id`：`341d7144-ad0b-59ce-84dc-87943e9f9415`
- page：289；chapter：高压系统；section：车载充电设备充电；subsection：操作步骤
- heading path：`高压系统 > 车载充电设备充电 > 操作步骤`
- 直接证据：`确认车辆已经处于熄火状态……打开充电盖……将三脚插头插合在家用220 V电源插座上……将充电枪完全插入车辆充电插座……充电枪被锁止后，车辆开始自动充电……充电结束后……`

该 gold 包含问题所需的完整、有顺序的车载充电操作流程。它在第一阶段候选中的排名为第 6（`dense_rank=4`、`bm25_rank=8`），因此没有进入无 rerank top-5，尽管它是有效候选。

| 无 rerank 排名 | chunk | page / section / subsection | RRF | dense rank | BM25 rank | 证据判断 / 文本片段 |
|---:|---|---|---:|---:|---:|---|
| 1 | `20e9e37d…` | 295 / 随车设备快速充电 / 操作步骤 | 0.032018 | 1 | 4 | 快速充电警告/操作内容，不是问题要求的车载充电设备流程。 |
| 2 | `89ebd4d2…` | 297 / 预约充电 / N/A | 0.031746 | 3 | 3 | 预约充电设置，与充电意图相关，但任务不同。 |
| 3 | `a6b45c33…` | 289 / 车载充电设备充电 / N/A | 0.031545 | 6 | 1 | 充电设备存放和 LED 状态内容；同一 section，但不是完整操作步骤。 |
| 4 | `61e1bf2d…` | 290 / 车载充电设备充电 / 操作步骤 | 0.031281 | 2 | 6 | 220V 电源安全约束；相关但不能独立提供操作顺序。 |
| 5 | `7c1fa4b5…` | 344 / 电池电量较低 / N/A | 0.030769 | 5 | 5 | 低电量/跨接启动参考内容，不是车载充电设备使用流程。 |

**Rerank 重放 top-5**

| rerank 排名 | chunk | 原始排名 | rerank score | 判断 |
|---:|---|---:|---:|---|
| 1 | `61e1bf2d…` | 4 | 0.997737 | 同 section 的安全片段排在完整操作流程之前。 |
| 2 | `341d7144…` **gold** | 6 | 0.995519 | 完整操作流程被恢复到 top-2。 |
| 3 | `20e9e37d…` | 1 | 0.992341 | 快速充电内容。 |
| 4 | `7c1fa4b5…` | 5 | 0.990439 | 低电量参考内容。 |
| 5 | `5bbab679…` | 8 | 0.983366 | 快速充电操作流程，不是车载充电设备流程。 |

**结论：** 这不是语料缺失问题。top 候选包含充电相关词和同 section 安全内容，真正完整的操作流程在第一阶段 RRF 中排名较低。rerank 将 gold 提升到第 2 位并修复 top-5 召回，但关键词丰富的长安全片段仍然排在 top-1。

### `abs_fault_handling_001`

**问题：** 制动防抱死系统发生故障时应该怎么办？
**主要分类：** `RRF_RANKING`，同时存在 `SAME_SECTION_COMPETITION` 和 `PARTIAL_EVIDENCE_COMPETITION`。

**当前 gold evidence**

- `chunk_id`：`7ec78836-badf-5bb4-9c66-ecfe4997b4c0`
- page：157；chapter：启动和驾驶；section：制动防抱死系统；subsection：功能状态说明
- heading path：`启动和驾驶 > 制动防抱死系统 > 功能状态说明`
- 直接证据：`警告！防抱死制动系统存在故障时，请立刻在安全区域停车并联系 Lynk & Co领克中心。`

该直接处置建议在第一阶段候选中排名第 7（`dense_rank=5`，未进入 BM25 top 候选），因此无 rerank top-5 只有系统说明和故障指示灯内容，没有能够独立表达处置动作的 chunk。

| 无 rerank 排名 | chunk | page / section / subsection | RRF | dense rank | BM25 rank | 证据判断 / 文本片段 |
|---:|---|---|---:|---:|---:|---|
| 1 | `b6c3943e…` | 157 / 制动防抱死系统 / N/A | 0.032266 | 3 | 1 | 解释 ABS 如何防止车轮抱死；没有故障处置动作。 |
| 2 | `b2a7d86e…` | 157 / 制动防抱死系统 / 功能状态说明 | 0.030886 | 1 | 9 | 说明故障时警告灯点亮；没有停车/联系服务中心的建议。 |
| 3 | `c2be2282…` | 166 / N/A / N/A | 0.030415 | 2 | 10 | 一般警告灯内容；缺少 ABS 专属处置动作。 |
| 4 | `86d51ecf…` | 157 / 制动防抱死系统 / N/A | 0.029851 | 7 | 7 | 正常制动踏板振动说明，不是故障响应。 |
| 5 | `1553e020…` | 229 / 泊车紧急制动系统 / N/A | 0.015873 | N/A | 3 | 不同子系统的泊车紧急制动限制。 |

**Rerank 重放 top-5**

| rerank 排名 | chunk | 原始排名 | rerank score | 判断 |
|---:|---|---:|---:|---|
| 1 | `7ec78836…` **gold** | 7 | 0.995860 | 正确提升了直接故障处置建议。 |
| 2 | `b2a7d86e…` | 2 | 0.9854 | 只有故障指示灯事实。 |
| 3 | `c2be2282…` | 3 | 0.9854 | 只有故障指示灯事实。 |
| 4 | `b6c3943e…` | 1 | 0.9770 | ABS 功能定义。 |
| 5 | `86d51ecf…` | 4 | 0.8728 | ABS 正常工作表现。 |

**结论：** 证据存在于候选集合，但被 RRF 排名和 BM25 词项竞争压到 top-5 之外。rerank 在没有新增生产规则的情况下将正确处置动作恢复到 top-1。

## 唯一的 rerank Hit@3 失败

### `high_voltage_label_001`

**问题：** 高压警告标签提示不要做什么？
**分类：** `RERANK_REGRESSION` 和 `PARTIAL_EVIDENCE_COMPETITION`；baseline 同时体现 `SAME_SECTION_COMPETITION`。

**当前 gold evidence**

- `chunk_id`：`9483bddf-8a95-5eb9-899f-062b3dab1d86`
- page：287；chapter：高压系统；section：高压警告标签；subsection：N/A
- heading path：`高压系统 > 高压警告标签`
- 直接证据：`高电压部件上贴有标签。切勿触摸、拆解或更换此类部件。`

| 无 rerank 排名 | chunk | page / section / subsection | RRF | dense rank | BM25 rank | 判断 |
|---:|---|---|---:|---:|---:|---|
| 1 | `7bea67b0…` | 287 / 高压警告标签 / N/A | 0.032522 | 1 | 2 | 要求遵守标签并避免物理接触；相对于“触摸/拆解/更换”完整要求不完整。 |
| 2 | `1f49b7d3…` | 304 / 保养和维护动力电池 / N/A | 0.032018 | 4 | 1 | 说明非专业人员不得触摸、移动或拆解动力电池/高压线缆；相关但不是标签原文的完整要求。 |
| 3 | `9483bddf…` **gold** | 287 / 高压警告标签 / N/A | 0.031514 | 2 | 5 | 包含三个禁止动作的完整标签事实。 |
| 4 | `4790312e…` | 305 / 低压蓄电池 / N/A | 0.015873 | N/A | 4 | 蓄电池注意事项，不是高压标签证据。 |
| 5 | `56cf9921…` | 200 / 后方交叉碰撞警告 / N/A | 0.015873 | N/A | 3 | 无关警告功能。 |

**Rerank 重放 top-5**

| rerank 排名 | chunk | 原始排名 | rerank score | 判断 |
|---:|---|---:|---:|---|
| 1 | `1f49b7d3…` | 2 | 0.986092 | 广义高压禁止事项，但不是当前标签完整表述。 |
| 2 | `7bea67b0…` | 1 | 0.973255 | 同 section 的标签指导内容，仍不完整。 |
| 3 | `e02d2d11…` | 7 | 0.940086 | 高压水枪清洗警告，任务错误。 |
| 4 | `9483bddf…` **gold** | 3 | 0.920952 | 精确标签原文被降到 top-3 之外。 |
| 5 | tire-warning chunk | N/A | 0.636698 | 无关警告上下文。 |

**结论：** cross-encoder 似乎更重视 `高压`、`警告` 和禁止动作之间的广泛语义重合，而不是标签场景下的精确指令。这是针对当前严格 gold 的真实 rerank regression，不是召回失败。

## Rerank Regression

| Case | baseline 排名 | rerank 排名 | 主要分类 | 新 top-1 不是校准证据的原因 |
|---|---:|---:|---|---|
| `tire_pressure_alarm_001` | 1 | 2 | `RERANK_REGRESSION`、`SAME_SECTION_COMPETITION` | 新 top-1（`bb2e2612…`，p62）覆盖 TPMS 故障/高胎压条件；gold `9843960b…` 给出低胎压恢复步骤：冷态充气至标准胎压后，以 30 km/h 以上行驶几分钟。 |
| `high_voltage_label_001` | 3 | 4 | `RERANK_REGRESSION`、`PARTIAL_EVIDENCE_COMPETITION` | 更宽泛的高压禁止事项和同 section 建议排在精确标签陈述之前。 |
| `brake_warning_lights_001` | 1 | 2 | `RERANK_REGRESSION`、`SEMANTIC_MISMATCH` | 新 top-1 `9367a45e…` 描述转向助力红/黄警告条件；gold `bb5eda8a…` 描述制动系统红/黄警告灯区别。 |

### Regression 证据细节

#### `tire_pressure_alarm_001`

- 问题：胎压报警后应该怎么办？
- Gold `9843960b…`，p62，`驾驶前的准备 > 胎压监测系统 > 胎压低报警`：冷态充气至标准胎压后，以 30 km/h 以上行驶几分钟，解除低胎压警告。
- Baseline：gold 排名第 1，RRF `0.032787`（`dense_rank=1`、`bm25_rank=1`）。
- Rerank：`bb2e2612…` 变为第 1（`0.991963`，原始排名第 2）；gold 变为第 2（`0.988520`，原始排名第 1）。
- `bb2e2612…` 是相关 TPMS 内容，但处理的是系统故障/高胎压场景，不能独立回答当前 gold 所定义的低胎压恢复问题。

#### `brake_warning_lights_001`

- 问题：制动系统红色和黄色警告灯分别在什么情况下点亮？
- Gold `bb5eda8a…`，p155，`启动和驾驶 > 制动系统 > 功能`：红色对应制动液液位低、传感器故障或电子制动力分配故障；黄色对应制动系统故障。
- Baseline：gold 排名第 1，RRF `0.032787`（`dense_rank=1`、`bm25_rank=1`）。
- Rerank：转向助力 chunk `9367a45e…` 排名第 1（`0.995391`，原始排名第 3）；gold 变为第 2（`0.994980`，原始排名第 1）。
- 这是系统身份识别失败：红/黄颜色条件的措辞高度相似，但对应系统错误。

## Rerank 非 top-1 汇总（10 条）

| Case | Gold rerank 排名 | Top-1 类型 | 主要解释 |
|---|---:|---|---|
| `seatbelt_usage_001` | 2 | 安全带作用，p99 | 宽泛使用问题与操作/警告证据发生作用域竞争。 |
| `tire_pressure_alarm_001` | 2 | 同 TPMS section，p62 | 故障/高胎压片段排在低胎压恢复步骤之前。 |
| `onboard_charging_steps_001` | 2 | 同充电设备 section，p290 | 安全片段排在完整流程之前。 |
| `high_voltage_label_001` | 4 | 广义高压蓄电池警告，p304 | 精确标签证据被广义禁止事项的语义重合压低。 |
| `wiper_caution_001` | 2 | 后雨刮注意事项，p65 | 另一部件/页面下的近似相同注意事项竞争（`DUPLICATE_COMPETITION`）。 |
| `fuel_safety_001` | 2 | 加油操作步骤，p162 | 操作片段与更宽泛的易燃性警告竞争。 |
| `epb_enable_release_001` | 2 | EPB 替代释放方式，p158 | 窄范围释放模式与启用/释放多部分问题竞争。 |
| `brake_warning_lights_001` | 2 | 转向助力警告，p155 | 系统错误但红/黄条件措辞相似。 |
| `rpa_safety_001` | 2 | RPA 退出条件，p236 | 同一功能，但操作条件片段不是宽泛安全证据。 |
| `pressure_wash_warning_001` | 2 | 高压清洗注意事项，p317 | 较短的直接注意事项与更宽泛的警告块竞争。 |

## Rerank 改善的 19 条 Case

rerank 的主要收益是**排序改善**，而不是召回范围扩大。它将原本位于第 2--5 位的证据移到 top-1；其中两条 case 从 baseline top-5 之外恢复。

| Case | Baseline gold 排名 | Rerank gold 排名 |
|---|---:|---:|
| `seatbelt_usage_001` | 4 | 2 |
| `seatbelt_fastening_001` | 2 | 1 |
| `tire_pressure_label_001` | 2 | 1 |
| `onboard_charging_steps_001` | N/A | 2 |
| `front_hood_open_001` | 2 | 1 |
| `front_hood_close_warning_001` | 2 | 1 |
| `fuel_safety_001` | 5 | 2 |
| `keyless_entry_unlock_001` | 3 | 1 |
| `keyless_entry_lock_001` | 4 | 1 |
| `lock_auto_window_close_001` | 2 | 1 |
| `automatic_wiper_sensor_001` | 2 | 1 |
| `remote_key_start_001` | 3 | 1 |
| `abs_fault_handling_001` | N/A | 1 |
| `autohold_explanation_001` | 2 | 1 |
| `slope_parking_warning_001` | 2 | 1 |
| `parking_emergency_brake_fault_001` | 3 | 1 |
| `apa_exit_conditions_001` | 2 | 1 |
| `fuse_box_location_001` | 2 | 1 |
| `vin_location_001` | 2 | 1 |

排名移动分布：11 条从 `2→1`，3 条从 `3→1`，1 条从 `4→1`，1 条从 `4→2`，1 条从 `5→2`，另有 2 条从 baseline top-5 之外恢复（`N/A→1/2`）。这支持已有结论：rerank 能改善早期证据排序，但必须结合其延迟成本和失败模式评估。

## 潜在 Gold 等价性复核

本节是**人工决策队列**，不是修改 benchmark 的指令。任何变更都必须复核 case 的答案 contract 和原始手册证据，而不能依据检索排名。

| Case | 当前严格 gold | 需要人工复核的候选 | 判断 |
|---|---|---|---|
| `onboard_charging_steps_001` | `341d7144…`，完整车载充电操作流程 | `61e1bf2d…`，p290，同 section/subsection | **不等价。** 它提供充电安全约束，不是完整的正常充电操作流程。保持严格 gold。 |
| `abs_fault_handling_001` | `7ec78836…`，安全停车并联系服务中心 | `b2a7d86e…` / `c2be2282…`，故障灯说明 | **不等价。** 它们识别故障指示，但缺少问题要求的处置动作。保持严格 gold。 |
| `high_voltage_label_001` | `9483bddf…`，不得触摸/拆解/更换带标签的高压部件 | `1f49b7d3…`，p304，不得触摸/移动/拆解动力电池和高压线缆 | **需要复核潜在等价性。** 它独立回答了“不要做什么”的大部分内容，但遗漏“更换”，且不属于标签 section。未经人工决定，不将其加入 `ANY_OF` gold。 |
| `wiper_caution_001` | 前雨刮注意事项 chunk | `62db6352…`，后雨刮注意事项 | **需要复核潜在重复等价性。** 注意事项文本近似相同，但对应不同部件。除非问题 contract 明确与部件无关，否则保持当前严格 gold。 |
| `pressure_wash_warning_001` | 更完整的高压清洗警告 | `bae2327c…`，同 page/section，操作压力和喷射距离注意事项 | **需要复核潜在部分等价性。** 它直接相关，但可能不能覆盖较宽的安全 contract。不自动扩大 gold。 |

## 主要瓶颈

证据通常存在于候选集合中，但第一阶段排序和 cross-encoder 排序都难以区分**完整、条件明确的证据**与**同系统、关键词丰富但仅部分相关的证据**。两个无 rerank Hit@5 miss 的精确 gold 分别位于候选第 6 和第 7 位；rerank 可以恢复它们。三条 rerank regression 则反映了反向问题：广泛语义相似度可能压过更精确的子系统或条件事实。

这并不足以证明现在应继续增加检索补丁。当前 dev set 规模有限，失败原因混合了 query scope、chunk 粒度、功能歧义和严格 gold 定义等因素。

## 调优建议

1. **不要仅根据本次复盘修改生产排序。** 保持 rerank 可选且默认关闭，并继续同时考虑其 top-1 收益、延迟成本和失败模式。
2. **将本报告的 taxonomy 用于更广泛的失败复核和后续冻结集评测。** 在提出模型或 chunking 变更前，先区分同 section 部分证据竞争与严格 gold/重复内容等价性问题。
3. **优先完善诊断产物持久化。** 后续评测结果应保存候选级 metadata 和 rerank score，减少对只读重放的依赖。这属于诊断改进，不是检索规则。

## 结果解读说明

指标是在 V3.5 retrieval benchmark 重校准后重新计算的；与 legacy 报告之间的差异，可能来自评测标签修正，而不是生产检索发生了回归或提升。本报告不对生产行为作出超出当前 rerank/no-rerank 对比的结论。
