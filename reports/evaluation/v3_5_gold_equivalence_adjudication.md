# V3.5 Gold Equivalence Adjudication

## Executive Summary

本报告对以下 5 条 case 进行统一的 evidence-level gold 等价性审核：

- `onboard_charging_steps_001`
- `abs_fault_handling_001`
- `high_voltage_label_001`
- `wiper_caution_001`
- `pressure_wash_warning_001`

本次仅生成 adjudication 报告，不修改 `data/eval/manual_eval_set.jsonl`，不修改 evaluator，也不修改 production RAG。完整 chunk 内容来自当前 V3.5 BM25 indexed chunk store；no-rerank / rerank rank 来自已生成的 V3.5 recalibrated reports。候选 metadata 和完整文本通过当前索引读取，未根据排名反向定义 gold。

结论：

- `onboard_charging_steps_001`：candidate 只包含安全约束，不包含完整车载充电流程，判定为 `PARTIAL_EVIDENCE`。
- `abs_fault_handling_001`：两个 candidate 只说明故障灯点亮，不包含停车和联系服务中心的处置动作，均判定为 `PARTIAL_EVIDENCE`。
- `high_voltage_label_001`：candidate 是更宽泛的高压部件安全禁止事项，遗漏当前问题要求的“更换”，判定为 `BROADER_BUT_INCOMPLETE`。
- `wiper_caution_001`：问题本身未限定前雨刮或后雨刮，候选与 gold 包含相同完整冬季使用注意事项，判定为 `DUPLICATE_EQUIVALENT`，建议加入等价 gold，但暂不修改 benchmark。
- `pressure_wash_warning_001`：candidate 仅覆盖设备压力、喷射距离和软材料注意事项，无法独立覆盖完整高压清洗安全 contract，判定为 `PARTIAL_EVIDENCE`。

因此，5 条 case 中 4 条建议保持当前 strict gold，1 条存在可接受的等价 gold 候选。正式 benchmark 是否加入 `wiper_caution_001` 的后雨刮 chunk，仍需人工确认后再单独修改、validation 和重跑指标。

## Adjudication Standard

本次判断的问题是：candidate 是否能够在不依赖其他 chunk 的情况下，独立、完整、正确地满足该 retrieval case 定义的 evidence target。

“主题相关”“包含部分事实”“排名靠前”都不足以成为等价 gold 的依据。只有以下两类 candidate 可以考虑加入 ANY_OF gold set：

- `FULLY_EQUIVALENT`：在当前问题 scope 下独立、完整、正确地满足 target。
- `DUPLICATE_EQUIVALENT`：来自不同 page 或 boundary，但实际上是相同事实的重复表达，并且可以独立完整回答当前问题。

`PARTIAL_EVIDENCE`、`CONTEXTUALLY_DIFFERENT`、`BROADER_BUT_INCOMPLETE` 和 `NOT_EQUIVALENT` 均不加入 ANY_OF gold。排名只用于复盘候选位置，不用于定义 gold。

## Case 1: `onboard_charging_steps_001`

### Question

如何使用车载充电设备给车辆充电？

### Retrieval Target

一个独立正确的 retrieval target 至少需要覆盖车载充电设备的主要完整流程：

- 确认车辆处于熄火状态；
- 解锁并打开充电盖，取下保护盖；
- 连接家用 220 V 电源；
- 将充电枪插入车辆充电插座并锁止，开始充电；
- 充电完成后按顺序断开充电枪和电源，并收好设备。

只有安全约束、充电状态说明、预约充电或快速充电流程，不能独立满足该 target。

### Current Gold

- chunk_id：`341d7144-ad0b-59ce-84dc-87943e9f9415`
- page：289；chapter：高压系统；section：车载充电设备充电；subsection：操作步骤
- heading_path：`高压系统 > 车载充电设备充电 > 操作步骤`
- no-rerank rank：6；rerank rank：2
- 完整 chunk.text：

```text
操作步骤
1 确认车辆已经处于熄火状态。
2 长按仪表板上的
按钮，解锁充电盖。
3 打开充电盖，并取下充电插座保护盖。
4 将三脚插头插合在家用220 V电源插座上。
按住充电枪上的按钮。
取下充电枪保护盖。
按住充电枪上的按钮，将充电枪完全插入车辆充电插座后松开
按钮，充电枪被锁止后，车辆开始自动充电。
6 充电结束后，解锁车辆，按住充电枪上的按钮，拔出充电枪。
7 从家用220 V电源插座上拔下三脚插头。
8 装回充电插座保护盖并关上充电盖，将充电设备放回原位。
```

### Candidate

- candidate chunk_id：`61e1bf2d-2ea6-5adf-951c-93565b650ce0`
- page：290；chapter：高压系统；section：车载充电设备充电；subsection：操作步骤
- heading_path：`高压系统 > 车载充电设备充电 > 操作步骤`
- no-rerank rank：4；rerank rank：1
- 完整 chunk.text：

```text
操作步骤
警告！
■按照适用的地方性和国家标准建议，采用220 V交流插座对动力
电池进行充电，充电电流不得超过允许的最大电流。
■禁止使用明显磨损或损坏的电源插座。
■禁止使用延伸电缆/移动插座。
■为避免损坏车漆，例如在大风情况下，将充电枪的保护盖放置在
合适位置，使其不接触车辆。
■充电前请确保三脚插头插合在家用220 V电源带接地的三孔插座
上。
■确保充电电缆或插头未被阳光直射。如被阳光直射，控制单元或
插头中的过热保护极有可能限制或中断充电。
■充电时，切勿从电源插座上拔下充电电缆。
■使用车载充电设备充电时，务必明确安全操作及警告事项。
```

### Evidence Comparison

| Dimension | Current Gold | Candidate | Equivalent? |
|---|---|---|---|
| Question scope | 车载充电设备的完整使用流程 | 车载充电设备的安全约束 | 否 |
| Object/system | 车载充电设备、车辆充电插座 | 车载充电设备、220 V 电源、电缆 | 部分一致 |
| Conditions | 熄火、连接、锁止、开始和结束充电 | 合规插座、接地、过热、禁止拔线 | 仅部分一致 |
| Required actions/facts | 覆盖连接、充电、断开、收纳完整顺序 | 没有实际开始/结束充电步骤 | 否 |
| Safety constraints | 流程中的设备连接和断开要求 | 多条 220 V 和电缆安全要求 | 候选更具体但不是同一 target |
| Missing facts | 无 | 解锁、打开充电盖、插入车辆、结束断开、收纳 | 是 |
| Extra facts | 设备操作步骤 | 电源标准、损坏插座、延伸电缆、阳光直射 | 不影响，但不能补足缺失流程 |

### Classification

`PARTIAL_EVIDENCE`

candidate 与 gold 属于同一 section，且提供了真实安全要求，但它不能独立回答“如何使用”的完整操作流程。不能因为同 section 或 rerank 排名第 1 就加入 ANY_OF gold。

### Recommendation

`KEEP_CURRENT_GOLD_ONLY`

### Counterfactual Impact

不适用。candidate 不属于 `FULLY_EQUIVALENT` 或 `DUPLICATE_EQUIVALENT`，因此不计算将其加入 gold 的指标影响。

## Case 2: `abs_fault_handling_001`

### Question

制动防抱死系统发生故障时应该怎么办？

### Retrieval Target

独立 target 必须至少包含：

- 明确指出 ABS/防抱死制动系统存在故障；
- 立即在安全区域停车；
- 联系 Lynk & Co 领克中心。

只说明故障灯点亮或系统发生故障，不能满足“应该怎么办”的处置要求。

### Current Gold

- chunk_id：`7ec78836-badf-5bb4-9c66-ecfe4997b4c0`
- page：157；chapter：启动和驾驶；section：制动防抱死系统；subsection：功能状态说明
- heading_path：`启动和驾驶 > 制动防抱死系统 > 功能状态说明`
- no-rerank rank：7；rerank rank：1
- 完整 chunk.text：

```text
功能状态说明
警告！
■防抱死制动系统存在故障时，请立刻在安全区域停车并联系Lynk
& Co领克中心。
■在崎岖、有碎石或有雪覆盖的道路上，制动距离将比在正常道路
时更长。
```

### Candidate 2A: `b2a7d86e...`

- candidate chunk_id：`b2a7d86e-8e79-5f5e-b2ea-bbc205bbc3ea`
- page：157；chapter：启动和驾驶；section：制动防抱死系统；subsection：功能状态说明
- heading_path：`启动和驾驶 > 制动防抱死系统 > 功能状态说明`
- no-rerank rank：2；rerank rank：2
- 完整 chunk.text：

```text
功能状态说明
防抱死制动系统存在故障时，该警告灯点亮。
```

### Candidate 2B: `c2be2282...`

- candidate chunk_id：`c2be2282-a6b3-5cab-a395-9a8c26c12541`
- page：166；chapter：启动和驾驶；section：制动防抱死系统；subsection：功能状态说明
- heading_path：`启动和驾驶 > 制动防抱死系统 > 功能状态说明`
- no-rerank rank：3；rerank rank：3
- 完整 chunk.text：

```text
功能状态说明
防抱死制动系统存在故障时，该警告灯点亮。
```

### Evidence Comparison

| Dimension | Current Gold | Candidate 2A / 2B | Equivalent? |
|---|---|---|---|
| Question scope | 故障发生后的处置方式 | 故障状态与警告灯状态 | 否 |
| Object/system | 防抱死制动系统 | 防抱死制动系统 | 是 |
| Conditions | 系统存在故障 | 系统存在故障 | 是 |
| Required actions/facts | 安全区域停车、联系领克中心 | 仅说明警告灯点亮 | 否 |
| Safety constraints | 立即停车并联系服务中心 | 没有处置或安全动作 | 否 |
| Missing facts | 无 | 停车、联系服务中心 | 是 |
| Extra facts | 第二条道路制动距离警告 | 无关键额外处置事实 | 不影响缺失 |

### Classification

Candidate 2A 和 2B 均为 `PARTIAL_EVIDENCE`。

它们在系统、page 和 section 上与 gold 接近，但只有故障指示事实，不包含回答“应该怎么办”所需的动作。两个 candidate 都不能加入 ANY_OF gold。

### Recommendation

对 candidate 2A、2B 均为 `KEEP_CURRENT_GOLD_ONLY`。

### Counterfactual Impact

不适用。两个 candidate 都不是等价 gold，正式指标不应按它们重新计算。

## Case 3: `high_voltage_label_001`

### Question

高压警告标签提示不要做什么？

### Retrieval Target

独立 target 必须对应高压警告标签所表达的完整禁止事项：

- 高电压部件上贴有标签；
- 切勿触摸；
- 不得拆解；
- 不得更换此类部件。

问题限定的是标签语境。仅表达一般性的高压系统安全要求，或只覆盖其中部分禁止动作，不等价于当前 gold。

### Current Gold

- chunk_id：`9483bddf-8a95-5eb9-899f-062b3dab1d86`
- page：287；chapter：高压系统；section：高压警告标签；subsection：N/A
- heading_path：`高压系统 > 高压警告标签`
- no-rerank rank：3；rerank rank：4
- 完整 chunk.text：

```text
高电压部件上贴有标签。切勿触摸、拆解或更换此类部件。
```

### Candidate

- candidate chunk_id：`1f49b7d3-8af1-51ef-85ac-acb4f3c159fe`
- page：304；chapter：保养和维护；section：保养和维护动力电池；subsection：N/A
- heading_path：`保养和维护 > 保养和维护动力电池`
- no-rerank rank：2；rerank rank：1
- 完整 chunk.text：

```text
警告！
■非专业人士，请勿触碰、移动、拆解动力电池及相应的高压线
缆，或其他带有高压警示标识的部件。
■当车辆或动力电池起火时，迅速离开车辆至安全距离，请使用电
火专用灭火器，使用水灭火或不正确灭火器灭火可能会导致触
电。
```

### Evidence Comparison

| Dimension | Current Gold | Candidate | Equivalent? |
|---|---|---|---|
| Question scope | 高压警告标签提示的禁止事项 | 动力电池维护安全警告 | 否 |
| Object/system | 带标签的高电压部件 | 动力电池、高压线缆和其他高压警示部件 | 部分一致 |
| Conditions | 标签指示的一般禁止动作 | 非专业人士操作动力电池/高压线缆 | 条件不同 |
| Required actions/facts | 触摸、拆解、更换均禁止 | 触碰、移动、拆解禁止 | 缺少“更换” |
| Safety constraints | 针对带标签高压部件 | 维护人员身份和起火处置条件 | 语境不同 |
| Missing facts | 无 | 标签语境、禁止更换 | 是 |
| Extra facts | 无 | 起火撤离和灭火器要求 | 与当前问题无关 |

### Classification

`BROADER_BUT_INCOMPLETE`

candidate 提供了更宽泛且真实的高压安全禁止事项，但遗漏当前问题要求的“更换”，且位于动力电池维护语境，不是高压警告标签本身。它不能因语义接近或 rerank top-1 而加入等价 gold。

### Recommendation

`KEEP_CURRENT_GOLD_ONLY`

### Counterfactual Impact

不适用。candidate 不是 `FULLY_EQUIVALENT` 或 `DUPLICATE_EQUIVALENT`。

## Case 4: `wiper_caution_001`

### Question

冬季使用雨刮前要注意什么？

问题没有限定“前雨刮”“后雨刮”或某个具体挡风玻璃部件。当前 `expected_sections` 为“前雨刮和洗涤器”，`acceptable_sections` 包含“后雨刮和洗涤器”，说明当前 benchmark contract 已允许后雨刮 section 作为可接受结构上下文，但原 evaluator 的 evidence hit 仍使用严格 gold chunk_id。

### Retrieval Target

一个独立 target 至少应完整覆盖冬季使用雨刮前的主要注意事项：

- 先清除挡风玻璃上的冰和积雪；
- 确认雨刮片没有冻结在挡风玻璃上。

由于问题是泛化的“雨刮”问题，而不是“前雨刮”专属问题，只要 candidate 在自身部件语境下完整表达相同冬季注意事项，即可考虑等价。

### Current Gold

- chunk_id：`32e9fad8-2056-5ffd-99b5-74871d62d66a`
- page：63；chapter：驾驶前的准备；section：前雨刮和洗涤器；subsection：N/A
- heading_path：`驾驶前的准备 > 前雨刮和洗涤器`
- no-rerank rank：2；rerank rank：2
- 完整 chunk.text：

```text
注意！
■冬季使用雨刮前，请先清除挡风玻璃上的冰和积雪并确认雨刮片
没有冻结在挡风玻璃上。
■当挡风玻璃上有尘沙、鸟粪、昆虫、树浆等异物时，请先清洁挡
风玻璃，否则会损坏雨刮片/影响雨刮片清洁效果。
■避免在挡风玻璃干燥的情况下开启雨刮，否则可能导致雨刮片和
挡风玻璃损坏。
■定期清洁和检查雨刮片，否则雨刮片使用寿命可能会缩短。
■应使用合格的洗涤液，不合格的洗涤液可能导致洗涤器损坏。
■如果发现雨刮片橡胶硬化或有裂纹、雨刮片在挡风玻璃上留下划
痕或不能刮洗某个区域，则需要更换雨刮片。
```

### Candidate

- candidate chunk_id：`62db6352-468d-5c6d-a527-c13f334becb1`
- page：65；chapter：驾驶前的准备；section：后雨刮和洗涤器；subsection：N/A
- heading_path：`驾驶前的准备 > 后雨刮和洗涤器`
- no-rerank rank：1；rerank rank：1
- 完整 chunk.text：

```text
注意！
■冬季使用雨刮前，请先清除挡风玻璃上的冰和积雪并确认雨刮片
没有冻结在挡风玻璃上。
■当挡风玻璃上有尘沙、鸟粪、昆虫、树浆等异物时，请先清洁挡
风玻璃，否则会损坏雨刮片/影响雨刮片清洁效果。
■避免在挡风玻璃干燥的情况下开启雨刮，否则可能导致雨刮片和
挡风玻璃损坏。
■定期清洁和检查雨刮片，否则雨刮片使用寿命可能会缩短。
■应使用合格的洗涤液，不合格的洗涤液可能导致洗涤器损坏。
■如果发现雨刮片橡胶硬化或有裂纹、雨刮片在挡风玻璃上留下划
痕或不能刮洗某个区域，则需要更换雨刮片。
```

### Evidence Comparison

| Dimension | Current Gold | Candidate | Equivalent? |
|---|---|---|---|
| Question scope | 泛化的冬季使用雨刮前注意事项，当前 gold 位于前雨刮 section | 同一泛化问题，位于后雨刮 section | 是 |
| Object/system | 前雨刮和洗涤器 | 后雨刮和洗涤器 | 部件不同，但问题未限定部件 |
| Conditions | 冬季使用雨刮前 | 冬季使用雨刮前 | 是 |
| Required actions/facts | 清除冰雪、确认未冻结，并包含其余注意事项 | 完整包含相同条目 | 是 |
| Safety constraints | 雨刮冻结、异物、干燥使用、清洁液等风险 | 完整重复表达 | 是 |
| Missing facts | 无 | 无 | 否 |
| Extra facts | 无 | 无实质额外事实 | 否 |

### Classification

`DUPLICATE_EQUIVALENT`

candidate 与 current gold 的正文内容完整相同，且当前问题没有限定前雨刮。两者仅在 section 和 page 上分别对应前、后雨刮；对于泛化的冬季雨刮注意事项问题，candidate 可以独立、完整回答同一 evidence target。

这不是仅凭文本相似度作出的判断：问题 scope 不限定部件，candidate 的完整正文也覆盖了当前 answer contract 的全部核心事实。若未来将问题改成“冬季使用前雨刮前要注意什么”，则该 candidate 将转为 `CONTEXTUALLY_DIFFERENT`，不应继续作为等价 gold。

### Recommendation

`ADD_CANDIDATE_AS_EQUIVALENT_GOLD`

建议未来在人工确认后，将 `62db6352-468d-5c6d-a527-c13f334becb1` 加入该 case 的 `gold_chunk_ids` / evidence gold 集合。本次不直接修改 `manual_eval_set`。

### Counterfactual Impact

只计算，不改变正式指标。

当前 candidate 排名：

- no-rerank：candidate rank 1，current gold rank 2；
- rerank：candidate rank 1，current gold rank 2。

若将 candidate 接受为等价 gold：

| 指标 | no-rerank 当前 | no-rerank 反事实 | rerank 当前 | rerank 反事实 |
|---|---:|---:|---:|---:|
| Hit@1 | 44/68 = 0.6471 | 45/68 = 0.6618 | 58/68 = 0.8529 | 59/68 = 0.8676 |
| Hit@3 | 63/68 = 0.9265 | 63/68 = 0.9265 | 67/68 = 0.9853 | 67/68 = 0.9853 |
| Hit@5 | 66/68 = 0.9706 | 66/68 = 0.9706 | 68/68 = 1.0000 | 68/68 = 1.0000 |
| MRR | 0.7848 | 0.7922 | 0.9203 | 0.9277 |

MRR 变化来自该 case 的 reciprocal rank 从 `1/2` 变为 `1/1`，即整体增加 `0.5 / 68`。该反事实影响不能作为加入 gold 的理由，只用于说明标注决策对历史指标的影响。

## Case 5: `pressure_wash_warning_001`

### Question

使用高压水枪清洗车辆时有哪些注意事项？

### Retrieval Target

当前 answer/retrieval contract 要求完整覆盖高压冲洗的主要安全事实：

- 清洗前确认车辆外部开闭件已正确关闭；
- 不得将水枪对准车辆底部接插件；
- 不要用高压清洗机或蒸汽清洗机直接清洁传感器，并保持至少 10 cm 距离；
- 喷嘴与车身表面至少保持 30 cm 距离并保持移动；
- 不得直接或间接冲洗发动机舱；
- 处理清洗后的制动效率风险。

一个只给出压力、喷射距离或软材料注意事项的 chunk，不能独立满足该完整 target。

### Current Gold

- chunk_id：`e02d2d11-fcdc-58ee-8f58-63557f557146`
- page：317；chapter：保养和维护；section：清洁车辆；subsection：高压冲洗
- heading_path：`保养和维护 > 清洁车辆 > 高压冲洗`
- no-rerank rank：2；rerank rank：2
- 完整 chunk.text：

```text
高压冲洗
警告！
■在清洗车辆后若要立即驾车，请数次踩下制动踏板，以去除制动
摩擦片上的水汽。水汽可能影响制动效率。
■洗车前，检查并确认车辆的外部开闭件已正确关闭。
■在清洗车辆时，禁止将水枪对准车辆底部接插件进行冲洗。
■避免用高压清洗机或蒸汽清洗机对传感器进行清洁，以免损坏传
感器。清洗车辆时应使用较小的水流短时间冲洗传感器表面，且
至少保持10 cm以上的距离。
■务必严格按高压清洗器使用说明清洁车辆，特别注意工作压力和
喷洗距离。如果使用压力清洗器，则喷嘴与车身的表面至少须保
持30 cm的距离。保持喷嘴移动，不要朝某个部位一直喷水，高
压水流浸入车辆零部件内可能导致损坏。
■请勿使喷嘴直接或间接对发动机舱内进行冲洗。高压水流会造成
发动机舱内的电气元件受损或造成一些部件不能正常使用。
```

### Candidate

- candidate chunk_id：`bae2327c-334a-59c5-bf4e-b5044ead3c6e`
- page：317；chapter：保养和维护；section：清洁车辆；subsection：高压冲洗
- heading_path：`保养和维护 > 清洁车辆 > 高压冲洗`
- no-rerank rank：1；rerank rank：1
- 完整 chunk.text：

```text
高压冲洗
使用高压水枪清洗车辆时，请务必遵照设备操作说明。特别是工作压
力和喷水距离。请勿使喷头过于靠近软材料，如橡胶软管或密封件。
```

### Evidence Comparison

| Dimension | Current Gold | Candidate | Equivalent? |
|---|---|---|---|
| Question scope | 高压水枪清洗车辆的完整注意事项 | 高压水枪清洗车辆的设备压力、喷水距离和软材料注意事项 | 否 |
| Object/system | 车辆高压冲洗 | 车辆高压冲洗 | 是 |
| Conditions | 清洗前、清洗中、清洗后及发动机舱/传感器条件 | 使用高压水枪时的设备说明和软材料距离 | 仅部分一致 |
| Required actions/facts | 开闭件、接插件、传感器、10 cm、30 cm、发动机舱、制动 | 遵守设备说明、注意压力和喷水距离、远离软材料 | 仅部分覆盖 |
| Safety constraints | 多条禁止和必须事项 | 一般设备操作要求 | 候选不完整 |
| Missing facts | 无 | 开闭件、底部接插件、传感器、发动机舱、制动等 | 是 |
| Extra facts | 清洗后制动处理等 | 软材料距离提示 | 不影响缺失 |

### Classification

`PARTIAL_EVIDENCE`

candidate 虽与 gold 同 page、section 和 subsection，且直接涉及高压水枪，但仅覆盖完整 warning block 中的一小部分。它不能独立回答“有哪些注意事项”的全部 target。

### Recommendation

`KEEP_CURRENT_GOLD_ONLY`

### Counterfactual Impact

不适用。candidate 不是等价 gold，不能依据其 rank 1 位置改变 benchmark 结果。

## Final Decision Table

| Case | Candidate | Classification | Recommendation | Metric Impact |
|---|---|---|---|---|
| `onboard_charging_steps_001` | `61e1bf2d-2ea6-5adf-951c-93565b650ce0` | `PARTIAL_EVIDENCE` | `KEEP_CURRENT_GOLD_ONLY` | 无；不属于等价 gold |
| `abs_fault_handling_001` | `b2a7d86e-8e79-5f5e-b2ea-bbc205bbc3ea` | `PARTIAL_EVIDENCE` | `KEEP_CURRENT_GOLD_ONLY` | 无；不属于等价 gold |
| `abs_fault_handling_001` | `c2be2282-a6b3-5cab-a395-9a8c26c12541` | `PARTIAL_EVIDENCE` | `KEEP_CURRENT_GOLD_ONLY` | 无；不属于等价 gold |
| `high_voltage_label_001` | `1f49b7d3-8af1-51ef-85ac-acb4f3c159fe` | `BROADER_BUT_INCOMPLETE` | `KEEP_CURRENT_GOLD_ONLY` | 无；不属于等价 gold |
| `wiper_caution_001` | `62db6352-468d-5c6d-a527-c13f334becb1` | `DUPLICATE_EQUIVALENT` | `ADD_CANDIDATE_AS_EQUIVALENT_GOLD` | 仅作反事实：no-rerank H1 +1、MRR +0.0074；rerank H1 +1、MRR +0.0074 |
| `pressure_wash_warning_001` | `bae2327c-334a-59c5-bf4e-b5044ead3c6e` | `PARTIAL_EVIDENCE` | `KEEP_CURRENT_GOLD_ONLY` | 无；不属于等价 gold |

## Benchmark Freeze Assessment

1. **保持 strict gold：** 4 条 case 建议保持当前 strict gold：车载充电、ABS 故障处置、高压警告标签、高压冲洗。
2. **真正 equivalent gold：** 当前发现 1 条明确的 `DUPLICATE_EQUIVALENT` 候选，即 `wiper_caution_001` 的后雨刮 chunk。
3. **仍需人工决定：** 1 条 case 需要 benchmark owner 确认是否接受“泛化雨刮问题”对应前/后雨刮的等价语义。如果确认问题 contract 确实不限定部件，则可加入候选；如果将问题解释为前雨刮专属，则应保持 strict gold。
4. **明确 false miss：** 在接受后雨刮 chunk 为等价 gold 的前提下，当前 `wiper_caution_001` 存在一个明确的 strict-chunk false miss：no-rerank 和 rerank 都已将完整等价 candidate 排在第 1，但当前 evaluator 因严格 chunk_id 仍将其判为非 gold。
5. **正式指标影响：** 只有接受该候选后，反事实指标才可能生效：no-rerank Hit@1 从 `0.6471` 到 `0.6618`，MRR 从 `0.7848` 到 `0.7922`；rerank Hit@1 从 `0.8529` 到 `0.8676`，MRR 从 `0.9203` 到 `0.9277`。Hit@3 和 Hit@5 不变。
6. **是否可以 freeze：** 在人工确认 `wiper_caution_001` 的问题 scope 和等价 gold 处理之前，不建议冻结 V3.5 Retrieval Benchmark。其余 4 条已具备明确的 strict-gold 决策，不构成阻塞。

如果人工接受该候选，下一步应单独完成：修改该 case 的 gold evidence、运行 benchmark validation、重新生成 no-rerank/rerank metrics，并保留 legacy report。此次报告不执行这些变更。
