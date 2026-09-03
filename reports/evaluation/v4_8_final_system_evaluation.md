# V4.8 Final System Evaluation

## 1. Executive Summary

V4.8 在不修改 retrieval、Prompt、context selection、Answer Model、evaluation semantics 或数据集的前提下，对当前 Resume-Ready 稳定配置完成了最终系统评测。

- V3.5 frozen retrieval benchmark 的 68 条 active cases 复跑结果与冻结指标完全一致：`Hit@1=0.6618`、`Hit@3=0.9265`、`Hit@5=0.9706`、`MRR=0.7922`。
- V4.8 使用 `qwen3.5:9b`、`think=false` 对 12-case answer dev diagnostic set 完成一次全量运行。
- V4.8 与 V4.7 选中模型正式运行的 Prompt Evidence identity/order/text 在 12/12 cases 上完全一致，raw answer 和 final answer 也在 12/12 cases 上逐字一致。
- 重新检查 V4.8 的 12 条最终答案后，PROPOSED Human Full Pass 为 `10/12`；存在 `1/12` severe failure、`1/12` unsupported claim 和 `1/12` critical safety omission。后三项均来自已有的 `abs_fault_warning_answer_001` evidence availability limitation，不是 V4.8 新增回归。
- 未发现新的 release-blocking regression。当前技术核心具备进入 V5.0 Resume Release 整理阶段的条件。

这些结论仅适用于当前单手册、当前冻结 benchmark、12-case dev diagnostic set 和本机运行环境，不代表 production accuracy、real-world accuracy 或跨车型泛化能力。

## 2. Final System Configuration

| 配置项 | 最终值 |
| --- | --- |
| Git branch | `exp/v4.8-final-system-evaluation` |
| Base commit | `65869746f56c676dfa1b9e162fba412c2c69d0eb` |
| Answer model | `qwen3.5:9b` |
| Model digest | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` |
| Parameters | 9.7B |
| Quantization | Q4_K_M |
| Model size | 6,594,474,711 bytes（约 6.6 GB） |
| Ollama version | `0.33.2` |
| stream | `false` |
| temperature | `0.0` |
| seed | `42` |
| think | `false` |
| Retrieval mode | `hybrid` |
| Rerank | `false` |
| top_k | `5` |
| Metadata context selection | `true` |
| Neighbor expansion | `false` |
| max_contexts | `5` |
| max_context_chars | `6000` |
| Embedding model | `BAAI/bge-small-zh-v1.5` |
| Answer evaluation semantics | `v4.3` |
| Answer dataset SHA-256 | `c3b06add0f3a906597a652997f824cd3c3cccc2e30eda684d6a98761ba493f8a` |
| Answer Prompt SHA-256 | `1c2ebcf4ee6f67d84e71c6dc7f29a670d017fcbfb80528c2f105d36fe4d9cdc0` |

本机 `.env` 未将模型覆盖回旧值；正式 artifact 记录的 effective model 为 `qwen3.5:9b`，effective think 为 `false`。

- **FINAL_CONFIGURATION_FROZEN = YES**
- **EFFECTIVE_FINAL_MODEL = `qwen3.5:9b`**
- **EFFECTIVE_FINAL_THINK = `false`**

## 3. Architecture Snapshot

当前稳定链路为：

```text
manual-aware parser/chunking
-> Chroma dense + BM25 sparse retrieval
-> RRF hybrid fusion
-> TOC/noise filtering + exact content dedup
-> metadata-aware context selection
-> final Evidence budget (5 contexts / 6000 chars)
-> stable grounded Answer Prompt
-> Ollama qwen3.5:9b direct answer (think=false)
-> answer sanitizer + citations
```

Rerank 保留为可选能力，但稳定默认仍为 `false`。本轮没有改动任何生产链路模块。

## 4. Retrieval Evaluation

评测集包含 69 条 records，其中 68 条 active、1 条 excluded。V4.8 以冻结配置复跑 hybrid no-rerank retrieval：

| Metric | V3.5 frozen | V4.8 verification | 是否一致 |
| --- | ---: | ---: | --- |
| Active cases | 68 | 68 | YES |
| Hit@1 | 0.6618 | 0.6618 | YES |
| Hit@3 | 0.9265 | 0.9265 | YES |
| Hit@5 | 0.9706 | 0.9706 | YES |
| MRR | 0.7922 | 0.7922 | YES |
| Elapsed | 21.11s | 19.80s | 仅运行记录，不作严格比较 |

未发现 retrieval severe regression。V4.8 没有重调 candidate count、RRF、BM25、filter、dedup 或 context selection。

## 5. Answer Evaluation

V4.8 对当前冻结的 12-case answer dev diagnostic set 运行一次完整评测。自动指标是 diagnostic proxy，不能替代 groundedness/correctness 的人工判断。

| Automated diagnostic | Result |
| --- | ---: |
| Case count | 12 |
| Non-empty answers | 12/12 |
| Internal-reference proxy failures | 0 |
| Forbidden-term failures | 0 |
| Must-include average coverage | 0.8081 |
| Expected-evidence hit proxy | 0.3636 |
| Insufficient-evidence lexical behavior pass | 0.0000 |
| Average elapsed per case | 19.43s |

`insufficient-evidence behavior pass=0.0000` 是已知 lexical proxy false negative：hard-negative 答案明确说明手册没有相关说明、无法提供操作步骤，但没有命中 evaluator 的固定 fallback phrase。该值不能解释为模型在 hard-negative case 上发生 hallucination。

## 6. Human Diagnostic Results

以下评分为对 V4.8 exact Prompt Evidence 和 final answer 的重新检查结果，沿用 V4.3 frozen rubric。由于 V4.8 与 V4.7 选中模型运行的 Evidence、raw answer、final answer 均逐条完全一致，评分结论与 V4.7 proposed review 一致。它们仍是 **PROPOSED**，不是新的 final human adjudication。

评分列依次为 Groundedness / Correctness / Completeness / Condition Handling / Safety Preservation。

| Case | PROPOSED scores | Full Pass | 关键判断 |
| --- | --- | --- | --- |
| `epb_enable_release_answer_001` | 2/1/0/2/2 | NO | Prompt 缺少正常启用 complementary evidence；答案边界克制，但无法完整回答启用步骤。 |
| `remote_key_start_answer_001` | 2/2/2/2/2 | YES | 正确区分普通启动与钥匙低电量/未识别时的 fallback 杯托流程。 |
| `pressure_wash_warning_answer_001` | 2/2/2/2/2 | YES | 安全距离、禁止冲洗部位和制动干燥要求均保留。 |
| `abs_fault_warning_answer_001` | 0/0/0/1/0 | NO | 专用立即停车 evidence 不在 Prompt；答案另加入“谨慎驾驶/避免急刹”等无直接依据建议。 |
| `abs_explanation_answer_001` | 2/2/2/2/2 | YES | ABS 功能与可见故障处理 evidence 使用正确。 |
| `autohold_explanation_answer_001` | 2/2/2/2/2 | YES | 正确说明短暂停车保持与起步解除关系。 |
| `overspeed_condition_answer_001` | 2/2/2/2/2 | YES* | 触发/解除方向正确；仍出现裸 `E1/E2/E4` 及额外限速偏差内容。 |
| `remote_start_blocked_answer_001` | 2/2/2/2/2 | YES | canonical 阻断条件完整。 |
| `epb_auto_subsection_answer_001` | 2/2/2/2/2 | YES | 直接回答静止并熄火后 EPB 自动启用，无无关程序扩展。 |
| `epb_poweroff_release_answer_001` | 2/2/2/2/2 | YES | 保留关闭 EPB AUTO 前置条件、两条释放路径及防溜车警告。 |
| `charging_led_list_answer_001` | 2/2/2/2/2 | YES | 八种 LED 状态和红灯处理完整。 |
| `unsupported_voice_brake_calibration_answer_001` | 2/2/2/2/2 | YES | 明确说明没有可靠手册依据，未拼接相关 Evidence 编造步骤。 |

PROPOSED aggregate（仅限 12-case dev diagnostic set）：

| Measure | Result |
| --- | ---: |
| Human Full Pass | 10/12 |
| Severe Failure | 1/12 |
| Unsupported Claim | 1/12 |
| Critical Safety Omission | 1/12 |

`*` 表示该 case 存在输出契约/回答范围限制，但按冻结 rubric 未构成 Full Pass 失败。

## 7. Safety / Unsupported Claims

- `abs_fault_warning_answer_001` 仍是唯一 PROPOSED critical safety omission。专用“立即在安全区域停车并联系领克中心”证据没有进入 Prompt Evidence，因此该问题同时包含 final-context availability limitation；模型还添加了无直接依据的谨慎驾驶建议。
- 七条历史 regression guards 均保持 PROPOSED Full Pass，未出现新的 hard-negative hallucination、列表缺项、方向反转或关键条件遗漏。
- V4.8 与 V4.7 选中模型运行的输出 12/12 exact match，因此没有新增 Unsupported Claim 或 Critical Safety Omission。
- 本轮按冻结原则记录历史已知问题，没有通过 Prompt、retrieval 或模型变更进行即时修复。

## 8. Reproducibility

V4.7 post-selection stability verification 已在当前环境对 4 个代表性 cases 各运行 3 次：

- Prompt Evidence identity/order/text：4/4 cases 全部 exact stable；
- raw answer：4/4 cases 全部 exact stable；
- final answer：4/4 cases 全部 exact stable；
- runtime：Ollama `0.33.2`；
- model/digest：`qwen3.5:9b` / `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`；
- generation：`temperature=0.0`、`seed=42`、`stream=false`、`think=false`。

此外，V4.8 单次全量运行与 V4.7 M1 正式运行在 12/12 cases 上满足：

| Comparison | Result |
| --- | --- |
| Case order | exact match |
| Prompt Evidence identity/order/text | 12/12 exact match |
| raw answer | 12/12 exact match |
| final answer | 12/12 exact match |

**FINAL_PROMPT_EVIDENCE_DRIFT = NO**。

该复现性结论只适用于当前硬件、Ollama 版本、模型 digest、generation configuration 和 inference backend，不代表跨硬件、跨 Ollama 版本或跨 backend 的 bit-for-bit determinism。

## 9. Answer Model Selection Rationale

V4.7 在 Prompt Evidence 12/12 invariant 的前提下比较 `qwen2.5:7b`、`qwen3.5:9b`、`gemma3:12b`。`qwen3.5:9b` 与 `gemma3:12b` 均修复两个主要 condition-handling targets，proposed quality 基本持平；`qwen3.5:9b` 模型更小，本地离线平均 elapsed 更低，且 normal/fallback 条件边界表达更清楚。

V4.8 不重新进行模型搜索，只验证已集成的最终系统。当前选择仍为 `qwen3.5:9b`。

## 10. Local Efficiency Observation

- V4.8 retrieval verification elapsed：19.80s（68 active queries）。
- V4.8 answer evaluation average elapsed：19.43s/case（12 cases）。
- V4.7 选型运行中 `qwen3.5:9b` average elapsed 为约 15.60s/case，模型文件约 6.6 GB。

上述数据来自不同时间的单次本地离线运行，可能受模型 warm state、系统负载和缓存影响。它们不是 production latency、SLA、吞吐、p50 或 p95 benchmark，不应用于严格性能回归结论。

## 11. Known Limitations

1. Answer evaluation 只有 12 条单手册 dev diagnostic cases，规模有限，不是外部 test set。
2. `epb_enable_release_answer_001` 存在 complementary-evidence availability limitation，模型看不到正常启用所需的完整 evidence。
3. `abs_fault_warning_answer_001` 存在 safety evidence availability limitation；当前 final context 未包含专用立即停车 instruction。
4. `qwen3.5:9b` 在 `overspeed_condition_answer_001` 中输出裸 `E1/E2/E4`。sanitizer 有意不全局删除裸 `E1`，以免误伤真实故障代码，这是已知 output-contract limitation。
5. 本地 elapsed 不是 production latency benchmark。
6. selected-model repeated-run stability 只在当前 hardware/backend、Ollama `0.33.2` 和固定 model digest 下验证。
7. retrieval benchmark 和 answer diagnostic set 均来自当前单手册 text-only corpus，不覆盖跨车型、图片、图标或复杂表格理解。
8. Query Rewrite 和 Embedding Model Benchmark 未纳入当前 Resume-Ready 版本；现有证据不足以将它们视为 release blocker。

## 12. What Was Explicitly Not Optimized

V4.8 没有进行以下优化：

- Prompt tuning；
- reranker tuning 或默认开启 rerank；
- embedding benchmark；
- query rewrite / multi-query / HyDE；
- context selection experiment；
- parser/splitter 重构；
- Answer Model 扩展搜索；
- case-specific fix；
- evaluation dataset、rubric 或 semantics 调整。

V4.6 rejected Condition Preservation Prompt delta 没有重新引入稳定系统。

## 13. Resume-Ready Assessment

| Gate | Status | Evidence / remaining work |
| --- | --- | --- |
| G1 Core RAG Pipeline | READY | ingest、retrieval、context、generation、citations 主链路已实现并测试。 |
| G2 Manual-Aware Processing | READY | hierarchy、subsection、heading path 和 chunk boundary 已在 V3.5 前完成修复与冻结。 |
| G3 Hybrid Retrieval | READY | dense + BM25 + RRF 可运行，默认 hybrid no-rerank。 |
| G4 Retrieval Evaluation | READY | 69 records / 68 active frozen benchmark，V4.8 复跑与冻结指标一致。 |
| G5 Answer Evaluation | READY | provenance、exact Prompt Evidence、raw/final answer、自动诊断和 frozen rubric 已建立。 |
| G6 Reproducible Generation | READY | 当前固定环境下 4 cases x 3 runs exact-output VERIFIED。 |
| G7 Controlled Failure-Driven Experiment | READY | V4.6 完成单变量实验并保留 REJECT 结论，未污染稳定 Prompt。 |
| G8 Answer Model Selection | READY | 三模型 controlled comparison 完成，`qwen3.5:9b` 已集成并验证。 |
| G9 Final End-to-End Evaluation | READY | V4.8 retrieval verification 与 12-case final answer evaluation 已完成。 |
| G10 Engineering Quality | READY | 分层、配置、测试、日志和评测 artifact 边界明确；最终测试结果见下文。 |
| G11 Demo / Usability | READY | FastAPI、Streamlit 和 CLI 基础链路已存在；本轮未做新的 UI 验收。 |
| G12 Portfolio Documentation | READY_FOR_V5 | 技术事实与阶段状态已同步；最终简历/展示包装留给 V5.0。 |
| G13 Git / Release Hygiene | READY_WITH_ACTION | 需精确提交 V4.8 文件并保留 unrelated dirty files，不得使用 `git add .`。 |
| G14 Resume / Interview Package | READY_FOR_V5 | 技术核心已具备，最终叙事、截图和项目包装留给 V5.0。 |

未完成 embedding benchmark、query rewrite 或新的 Prompt treatment 不构成 Resume-Ready blocker。

## 14. Global Information Sync Audit

| Surface | Decision | Action |
| --- | --- | --- |
| `README.md` | UPDATE_REQUIRED | 将 V4.8 从下一阶段改为已完成，并把下一阶段收敛为 V5.0 Resume Release。 |
| `AGENTS.md` | UPDATE_REQUIRED | 同步 V4.8 freeze 状态、release gates 和禁止继续混入优化变量。 |
| `docs/evaluation.md` | UPDATE_REQUIRED | 记录最终配置、retrieval verification、answer diagnostic 边界和下一阶段。 |
| `.env.example` | NO_UPDATE_NEEDED | V4.7 已同步 `qwen3.5:9b` 与 `think=false`，本轮配置未变。 |
| Config / CLI help | NO_UPDATE_NEEDED | effective model/think 与 artifact 一致，没有新增选项。 |
| Tests | NO_UPDATE_NEEDED | 本轮未修改 Python behavior；执行现有全量测试验证。 |
| Code comments/docstrings | NO_UPDATE_NEEDED | 无架构或行为变化。 |
| Historical V3.5/V4.4-V4.7 artifacts | NO_UPDATE_NEEDED | 保持冻结，不覆盖、不重解释。 |
| V4.8 artifacts | UPDATE_REQUIRED | 新增 final answer JSON/Markdown 与本总结报告。 |

## 15. Release Recommendation

当前系统满足以下条件：

- 最终配置与 V4.7 已接受选型一致；
- selected model 和 `think=false` 实际生效；
- frozen retrieval 复跑无指标漂移；
- 12-case final answer run 完成，Prompt Evidence 无 drift；
- 未发现新的重大 safety regression；
- 历史已知 limitations 已明确记录，不通过临时调参掩盖；
- production RAG behavior 在 V4.8 中保持不变。

因此建议结束 V4.8，进入 V5.0 Resume Release 的文档、演示、Git checkpoint 与项目包装工作，不再在本阶段追加技术优化。

- `FINAL_SYSTEM_EVALUATION_COMPLETE = YES`
- `RESUME_READY_TECHNICAL_CORE = YES`
- `RELEASE_BLOCKER_PRESENT = NO`
- `READY_FOR_V5_0_RESUME_RELEASE = YES`
