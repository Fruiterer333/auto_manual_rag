# V3.5 Retrieval Benchmark 总览

## 1. Freeze 状态

V3.5 Retrieval Benchmark 已完成：

1. chunk strategy 对齐；
2. benchmark recalibration；
3. consistency validation；
4. ambiguous-case adjudication；
5. failure review；
6. gold-equivalence adjudication；
7. final freeze。

本文件汇总当前正式状态，不覆盖 legacy 或 pre-freeze 历史报告。

## 2. Dataset 与 Index

| item | value |
| --- | ---: |
| total records | 69 |
| active cases | 68 |
| excluded cases | 1 |
| benchmark evidence | 99 |
| pending human review | 0 |
| validation issues | 0 |
| Chroma stored chunks | 1002 |
| BM25 / hygiene-filtered retrieval-eligible chunks | 981 |
| hygiene-filtered chunks | 21 |

Excluded case：`parking_detection_range_001`。

原因：`Required table values are not represented in the current text-only chunk corpus.`

该 case 保留在 dataset 中并设置 `excluded=true`，不进入 active denominator。它表示 text-only parser/table extraction coverage gap，不是 retrieval failure。

## 3. Gold Semantics

当前评测是与 V3.5 chunk strategy 绑定的 chunk-level retrieval benchmark。

- Gold chunk 必须存在于当前 V3.5 index，并能独立提供问题所需 evidence。
- Chunk strategy 实质变化后必须重新校准 benchmark。
- Multi-gold 使用 ANY_OF：命中任意 independently sufficient gold 即算 hit。
- MRR 使用排名最高的 gold chunk。
- Excluded case 不进入 Hit@k / MRR denominator。

当前明确的 multi-gold cases：

- `parking_emergency_brake_fault_001`：3 个 independently sufficient gold chunks；
- `charging_led_states_001`：2 个完整覆盖 8 种 LED 状态的 gold chunks；
- `wiper_caution_001`：2 个前/后雨刮 equivalent gold chunks。

## 4. Official Frozen Metrics

| mode | Hit@1 | Hit@3 | Hit@5 | MRR | elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hybrid no-rerank | 0.6618 | 0.9265 | 0.9706 | 0.7922 | 21.11s |
| Hybrid + rerank | 0.8676 | 0.9853 | 1.0000 | 0.9277 | 42.96s |

Rerank 将：

- Hit@1 从 `45/68` 提升到 `59/68`；
- Hit@5 从 `66/68` 提升到 `68/68`。

Rerank 明显改善 ranking quality，但仍存在少量 case-level regression。`ENABLE_RERANK=false` 继续作为默认配置。

Elapsed 只记录单次运行，不能用作严格 latency benchmark。正式 latency comparison 需要 warmup、同进程、重复运行、per-query latency 和 p50/p95。

## 5. Benchmark Evolution

| state | 解释 |
| --- | --- |
| legacy / pre-recalibration | 使用旧 chunk mapping、metadata 或 gold truth，只保留为历史记录。 |
| recalibrated pre-freeze | 已与 V3.5 index 对齐，但最后 gold-equivalence adjudication 尚未完成。 |
| frozen / official | 完成 recalibration、validation 和 adjudication 后的正式 baseline。 |

Pre-freeze → frozen 的变化：

- no-rerank Hit@1：`0.6471 -> 0.6618`；MRR：`0.7848 -> 0.7922`；
- rerank Hit@1：`0.8529 -> 0.8676`；MRR：`0.9203 -> 0.9277`；
- Hit@3 / Hit@5 不变。

这些变化来自 `wiper_caution_001` equivalent-gold adjudication，不是 production retrieval improvement。Legacy → recalibrated 的较大差异主要来自 benchmark truth 修正，也不能解释为 production regression。

## 6. Interpretation and Limitations

- Hybrid no-rerank top-5 为 `66/68`，candidate retrieval 已具有较高 recall，但并非完美。
- Hybrid + rerank top-5 为 `68/68`，主要收益在 ranking quality。
- 当前 benchmark 来自单本汽车手册，是 frozen V3.5 dev baseline，不是跨车型、跨品牌 final test benchmark。
- 当前系统是 text-only RAG，不覆盖依赖图片、图标、复杂表格或版面理解的问题。
- Retrieval freeze 不代表 answer generation、citation correctness 或 answer completeness 已经解决。
- 当前没有证据支持继续加入 HyDE、MultiQuery、query rewrite、额外 boosting 或 parser 特例。

## 7. Freeze Decision and Next Stage

V3.5 Retrieval 阶段已达到可复现、可验证、可审计的冻结状态。下一主阶段转向 V4 Answer Quality / Answer Evaluation：刷新 answer evidence provenance、建立正式 answer baseline、增加人工评分，并根据 groundedness、coverage、citation 和 forbidden-content failures 做改进。

正式 frozen artifacts：

- `v3_5_frozen_hybrid_no_rerank.json`；
- `v3_5_frozen_hybrid_rerank.json`；
- `v3_5_frozen_rerank_comparison.md`。
