# V4.1 Answer Sanitization & Evidence Leak Detection

## 问题

V4.0 pre-baseline audit 发现 QAChain 的 answer post-processing 在移除内部 Evidence 引用后，会无条件删除“根据”“参考”“参见”。因此正常句子可能被破坏：

```text
具体操作应根据车辆状态进行。
```

此前可能被清洗为：

```text
具体操作应车辆状态进行。
```

与此同时，Answer Evaluator 只检测了部分英文引用形式，无法识别 `E3证据`、`E5 证据`、`证据 E2`、`参照E3证据` 等真实泄漏形式。

## 根因

“根据”“参考”“参见”是普通中文连接词，不能作为独立删除目标。它们只在明确修饰 prompt 内部 Evidence ID 时才属于应清除的实现细节。

原 production sanitizer 与 evaluator detector 分别维护了不同的正则，导致清洗过宽、检测过窄，并且会随维护逐步漂移。

## 内部 Evidence Reference 定义

V4.1 将以下形式定义为内部 Evidence 引用：

- `Evidence E1`、`Evidence ID E1`
- `[EVIDENCE E1]`
- `E1 Evidence`
- `E3证据`、`E5 证据`
- `证据E2`、`证据 E4`
- 带连接词的上述形式，例如 `参照E3证据`、`参考 E2 证据`、`根据Evidence E4`、`根据 Evidence E5`、`参考[EVIDENCE E2]`
- 既有 legacy 形式：`手册片段2`、`资料4`、`片段4`、`上下文2`、`context 3`、`source id 3`

该定义不把裸 `E1` 或 `E10` 视为 internal reference。

## Production Sanitization

新增共享 helper：`app/rag/utils/internal_evidence_refs.py`。

- `contains_internal_evidence_reference()`：供 evaluator 判断是否泄漏；
- `strip_internal_evidence_references()`：供 QAChain 清除完整内部引用结构。

sanitizer 匹配并删除完整结构（可包含“根据/参考/参见/参照”、括号和紧邻逗号或冒号），而不是先删除普通连接词。删除后仅做局部空白、残留空括号和句首分隔符清理，不进行自然语言改写。

示例：

```text
根据 Evidence E3，电子驻车制动可以手动释放。
-> 电子驻车制动可以手动释放。

根据车辆状态选择相应功能。
-> 根据车辆状态选择相应功能。
```

## Evaluator Detection

`app/evaluation/answer_evaluator.py` 已改为复用共享 detector。production sanitizer 和 Answer Evaluation 因而使用同一套“内部 Evidence reference”定义。

可检测：`E3证据`、`E5 证据`、`参照E3证据`、`根据 Evidence E4`、`[EVIDENCE E2]` 等。

不会误判：

- `故障代码 E1 表示传感器异常。`
- `显示屏提示 E2。`
- `车辆采用 E1 级材料。`
- `根据车辆状态进行操作。`
- `具体要求请参考用户手册。`
- `参见保养章节。`

## False-Positive Protection

裸 `E<number>` 可能是故障代码、设备编号或材料等级。因此匹配必须同时有 `Evidence`、`证据`、方括号 Evidence 标记或 legacy 内部标签等强信号；实现没有使用裸 `E\d+` 作为独立 detector 或删除规则。

## Regression Tests

新增或扩展的回归测试覆盖：

- 正常中文中“根据/参考/参见”完整保留；
- 英文、中文、方括号和标点包裹的 Evidence 引用；
- 既有 legacy 内部标签；
- 裸 `E1`、`E10` 业务文本保留；
- evaluator 的 true/false leak detection 参数化用例；
- sanitizer 幂等性：`sanitize(sanitize(text)) == sanitize(text)`；
- 仅包含 `Evidence E1` 的文本可安全清洗为空字符串。

## Remaining Formal Baseline Blockers

V4.1 只消除了 sanitizer 安全性和 Evidence leak detection 两项 blocker。正式 V4 baseline 仍需要：

1. 保存实际发送给 LLM 的完整 Evidence snapshot，包括顺序和截断状态；
2. 保留 raw answer 与 post-processed answer 的可审计边界；
3. 处理 deterministic term normalization，例如 `10 cm` 与“10厘米”；
4. 定义并验证 human review rubric；
5. 人工复核 `remote_start_blocked_answer_001` 的宽泛 answer contract。

本轮没有运行正式 Answer Evaluation、retrieval evaluation 或 Ollama generation。
