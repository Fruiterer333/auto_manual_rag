# V4.7 Resume-Ready Answer Model Selection

## 1. Executive Summary

本实验在完全冻结 retrieval、context、prompt、dataset 和 evaluation semantics 的条件下，对三个本地 Answer Model 进行 12-case dev diagnostic 对比。三组运行的 Prompt Evidence 在全部 12 条 case 上实现 identity、order、text 精确一致，因此答案差异可归因于模型及其必要的模型级直接回答配置。

`qwen3.5:9b` 和 `gemma3:12b` 均修复了 `epb_poweroff_release_answer_001` 中遗漏“关闭 EPB AUTO”的关键前置条件，并将 `remote_key_start_answer_001` 的杯托流程保留在钥匙电量低/未识别的特殊情形下。`qwen3.5:9b` 对 normal/fallback 边界表达最清楚，资源成本又低于 `gemma3:12b`；最终人工决策已接受该模型，并完成稳定默认配置集成。

逐 case rubric 评分仍是 Codex proposed review，不冒充 final case-level human adjudication；用户已对最终模型选择作出 `ACCEPT` 决策。

**RECOMMENDED_MODEL = `qwen3.5:9b`**  
**KEEP_CURRENT_MODEL = NO**  
**ANSWER_MODEL_SELECTION_COMPLETE = YES**

## 2. Objective

判断当前 `qwen2.5:7b` 是否构成 grounded generation 能力瓶颈，以及更强本地模型带来的 condition handling、groundedness、completeness 收益是否值得额外资源成本。本轮不是大规模模型排行榜；模型比较阶段只改变 run-local Answer Model，最终确认后由独立 post-selection integration 更新 production 默认配置。

## 3. Git / Branch State

- Branch：`exp/v4.7-answer-model-selection`
- Base commit：`588ea481ddc35d68dc0341a61b02fa90dc06144b`
- Base subject：`record rejected v4.6 condition preservation experiment`
- V4.6 rejected prompt delta 不在稳定 prompt 中。
- 三组 artifact 均记录同一 base commit、同一 branch 和 dirty worktree 状态。
- 既有 `app/core/exceptions.py` 修改及历史 untracked docs/reports 未被本实验修改。

## 4. Candidate Models

| ID | Model tag | Digest | Parameters | Quantization | Local size |
| --- | --- | --- | --- | --- | ---: |
| M0 | `qwen2.5:7b` | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | 7.6B | Q4_K_M | 4.7 GB |
| M1 | `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 9.7B | Q4_K_M | 6.6 GB |
| M2 | `gemma3:12b` | `f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` | 12.2B | Q4_K_M | 8.1 GB |

选择理由：M0 是稳定基线；M1 是同生态能力升级；M2 提供跨模型家族比较。未扩大候选集合。

## 5. Frozen RAG Configuration

| Variable | Frozen value |
| --- | --- |
| Dataset SHA-256 | `c3b06add0f3a906597a652997f824cd3c3cccc2e30eda684d6a98761ba493f8a` |
| Evaluation semantics | `v4.3` |
| Retrieval | hybrid |
| Rerank | false |
| top_k | 5 |
| Metadata context selection | true |
| Neighbor expansion | false |
| max_contexts | 5 |
| max_context_chars | 6000 |
| Embedding | `BAAI/bge-small-zh-v1.5` |
| Answer prompt SHA-256 | `1c2ebcf4ee6f67d84e71c6dc7f29a670d017fcbfb80528c2f105d36fe4d9cdc0` |
| Ollama | `0.33.2` |
| stream | false |
| temperature | 0.0 |
| seed | 42 |
| timeout | 120 seconds |

Parser、chunking、Chroma、BM25、RRF、filters、dedup、ranking、context ordering、citation assembly、sanitizer、dataset 和 rubric 均未改变。

## 6. Generation / Template Compatibility

- M0：runtime 未声明 thinking capability；`think` 未设置，保持模型/runtime 默认。
- M1：runtime 声明 thinking capability。当前 production payload 在 `think` 未设置时的 smoke 请求超过 120 秒；使用 Ollama 原生顶层 `think=false` 后可稳定生成干净 final response。本次只对 M1 run 显式关闭 thinking，并完整记录该差异。
- M2：runtime 未声明 thinking capability；`think` 未设置。
- 三模型均使用 application-level `temperature=0.0`、`seed=42`、`stream=false`。模型自身 template/default sampler 语义并不因此完全相同，这是跨模型比较的固有限制。

**MODEL_COMPARABILITY_LIMITATION = YES**：M1 需要显式 `think=false` 才能形成可比的 direct-answer 模式，但该设置没有改变 Answer Prompt semantics，也没有把 reasoning trace 暴露给用户。

## 7. Smoke Gate

三个模型先使用同一 `abs_explanation_answer_001` 做非计分 warmup/smoke：

- 均返回非空答案和 5 条 citations；
- Prompt Evidence ID/order 完全一致；
- 未发现可见 reasoning/template marker；
- M1 仅在显式 `think=false` 后通过时限 gate。

随后每模型各运行一次完整 12-case formal controlled run，没有自动扩展为重复全量 benchmark。

## 8. Artifact Paths

- M0 JSON：`reports/evaluation/v4_7_answer_model_qwen2_5_7b_20260903_001.json`
- M0 Markdown：`reports/evaluation/v4_7_answer_model_qwen2_5_7b_20260903_001.md`
- M1 JSON：`reports/evaluation/v4_7_answer_model_qwen3_5_9b_20260903_001.json`
- M1 Markdown：`reports/evaluation/v4_7_answer_model_qwen3_5_9b_20260903_001.md`
- M2 JSON：`reports/evaluation/v4_7_answer_model_gemma3_12b_20260903_001.json`
- M2 Markdown：`reports/evaluation/v4_7_answer_model_gemma3_12b_20260903_001.md`

## 9. Prompt Evidence Invariance

| Gate | M0 vs M1 | M0 vs M2 |
| --- | --- | --- |
| Dataset hash equal | YES | YES |
| Semantics equal | YES | YES |
| Retrieval/context config equal | YES | YES |
| Prompt hash equal | YES | YES |
| Case count/order equal | YES | YES |
| Evidence identity exact match | 12/12 | 12/12 |
| Evidence order exact match | 12/12 | 12/12 |
| Evidence text exact match | 12/12 | 12/12 |

**PROMPT_EVIDENCE_INVARIANT = YES**。

## 10. Automated Metrics

以下均为 diagnostic proxy，不替代人工 groundedness/correctness 判断。

| Metric | M0 qwen2.5 | M1 qwen3.5 | M2 gemma3 |
| --- | ---: | ---: | ---: |
| case_count | 12 | 12 | 12 |
| answer_non_empty_pass | 12 | 12 | 12 |
| internal_reference_leak_count | 0 | 0 | 0 |
| forbidden_term_failure_count | 0 | 0 | 0 |
| must_include average coverage | 0.8535 | 0.8081 | 0.8308 |
| expected_evidence_hit_rate | 0.3636 | 0.3636 | 0.3636 |
| insufficient-evidence behavior pass | 1.0000 | 0.0000 | 1.0000 |

M1 的 hard-negative 答案明确说“没有说明/无法找到依据”，人工语义正确，但未命中 evaluator 的固定 fallback phrase，因此 `0.0000` 是 lexical proxy false negative。三个模型的 expected-evidence proxy 相同且偏低，不能用于区分模型能力。

自动 internal-reference 检查有意不删除/判定裸 `E1`，以免误伤真实故障代码。离线审阅发现：

- M0：无裸 Evidence ID；
- M1：`overspeed_condition_answer_001` 出现 `E1/E2/E4`；
- M2：`epb_enable_release_answer_001` 出现 `E1-E5`。

这是模型遵循输出约束的兼容性限制，不在本实验中通过扩大 sanitizer 或修改 prompt 修复。

## 11. Proposed Human Scores

以下为 Codex proposed review，沿用 V4.3 frozen rubric，不是 final human adjudication。

| Case | M0 G/C/Co/Ch/S | M1 G/C/Co/Ch/S | M2 G/C/Co/Ch/S | Proposed observation |
| --- | --- | --- | --- | --- |
| `epb_enable_release_answer_001` | 0/0/0/0/0 | 2/1/0/2/2 | 2/1/0/2/2 | 三者均受正常启用 Evidence 缺失限制；M1/M2 不再把紧急制动当作普通启用方法 |
| `remote_key_start_answer_001` | 1/0/2/0/2 | 2/2/2/2/2 | 2/2/2/2/2 | M1/M2 均恢复 normal/fallback 边界；M1 表达最明确 |
| `pressure_wash_warning_answer_001` | 2/2/2/2/2 | 2/2/2/2/2 | 2/2/2/2/2 | 关键距离、禁止部位和制动干燥均保留 |
| `abs_fault_warning_answer_001` | 1/0/0/1/0 | 0/0/0/1/0 | 1/0/0/1/0 | 三者都看不到专用立即停车 Evidence；M1 另推导“谨慎驾驶/避免急刹” |
| `abs_explanation_answer_001` | 2/2/2/2/2 | 2/2/2/2/2 | 2/2/2/2/2 | 功能说明正确 |
| `autohold_explanation_answer_001` | 2/2/2/2/2 | 2/2/2/2/2 | 2/2/2/2/2 | 短暂停车和起步关系正确 |
| `overspeed_condition_answer_001` | 2/2/2/2/2 | 2/2/2/2/2 | 2/2/2/2/2 | 核心触发/解除方向正确；M1 有额外限速偏差内容和裸 Evidence ID |
| `remote_start_blocked_answer_001` | 2/2/2/2/2 | 2/2/2/2/2 | 2/2/2/2/2 | canonical 阻断条件完整 |
| `epb_auto_subsection_answer_001` | 1/1/2/1/2 | 2/2/2/2/2 | 2/2/2/2/2 | M1/M2 均消除不必要程序扩展 |
| `epb_poweroff_release_answer_001` | 1/0/1/0/2 | 2/2/2/2/2 | 2/2/2/2/2 | M1/M2 均保留关闭 EPB AUTO 前置条件和两条路径 |
| `charging_led_list_answer_001` | 2/2/2/2/2 | 2/2/2/2/2 | 2/2/2/2/2 | 八种 LED 状态和红灯处理完整 |
| `unsupported_voice_brake_calibration_answer_001` | 2/2/2/2/2 | 2/2/2/2/2 | 2/2/2/2/2 | 三者均拒绝无依据语音校准步骤 |

Proposed aggregate（仅限 12-case dev diagnostic set）：

| Measure | M0 | M1 | M2 |
| --- | ---: | ---: | ---: |
| Human Full Pass | 7/12 | 10/12 | 10/12 |
| Severe Failure | 4/12 | 1/12 | 1/12 |
| Unsupported Claim | 4/12 | 1/12 | 1/12 |
| Critical Safety Omission | 1/12 | 1/12 | 1/12 |

M1/M2 对 `abs_fault_warning_answer_001` 的 critical omission 不能作为纯模型能力比较：立即停车的专用 evidence 没有进入 Prompt Evidence。

## 12. Primary Diagnostic: EPB Power-off Release

M0 漏掉第一条路径的“在中央显示屏关闭 EPB AUTO”。M1 和 M2 都完整保留该 prerequisite、N 挡、制动踏板、EPB 开关、START/STOP 两条路径及防溜车警告。

结论：M1/M2 相对 M0 均表现出明确的 prerequisite preservation 改善。

## 13. Primary Diagnostic: Remote-key Start

M0 把前杯托 fallback 流程列为普通启动第一步。M1 先给出普通启动条件和步骤，再把杯托流程明确放在“遥控钥匙电量低或系统无法检测到钥匙”的特殊情形。M2 也将杯托流程放到“未检测到钥匙”的条件下，但将该提示直接解释为电池电量低，表述比 Evidence 的联合条件略强。

结论：M1/M2 均有实质改善；M1 对 normal vs fallback 的适用条件最清楚。

## 14. Regression Guards

| Guard | M0 | M1 | M2 | Notes |
| --- | --- | --- | --- | --- |
| pressure wash | Full Pass | Full Pass | Full Pass | 安全距离与禁止项保留 |
| overspeed conditions | Full Pass | Full Pass* | Full Pass | M1 有裸 Evidence ID 和额外限速偏差段，但核心方向正确 |
| remote-start blocked | Full Pass | Full Pass | Full Pass | exhaustive list 保持 |
| ABS explanation | Full Pass | Full Pass | Full Pass | 无“所有路况缩短制动距离”错误 |
| Auto Hold explanation | Full Pass | Full Pass | Full Pass | 无全场景替代驾驶员泛化 |
| charging LED list | Full Pass | Full Pass | Full Pass | 八种状态完整 |
| unsupported voice calibration | Full Pass | Full Pass | Full Pass | hard negative 无伪造步骤 |

Proposed regression result：三模型均保持 7/7 guard Human Full Pass。`*` 表示存在非 rubric 致命的输出格式/范围限制，应由用户复核。

## 15. Unsupported Claim and Safety Comparison

- M0 的历史 condition failures 保留，proposed unsupported claim 为 4/12。
- M1/M2 的 condition target 均改善，proposed unsupported claim 降至 1/12，剩余项为 ABS fault。
- 三模型都没有恢复 ABS fault contract 要求的“立刻在安全区域停车”，因为该 evidence 对模型不可见。
- M1 在 ABS fault 中加入“谨慎驾驶、避免急刹”推导，风险高于 M2；该 case 不应被用来奖励任一模型。
- 未发现 M1/M2 在七条 guards 上新增 critical safety omission。

## 16. Retrieval-limited Case Caveats

- `epb_enable_release_answer_001`：Prompt 缺正常“拉起 EPB 开关”的 complementary Evidence。M1/M2 的答案边界更克制，但不能凭模型补齐不存在的步骤。
- `abs_fault_warning_answer_001`：专用“立即在安全区域停车并联系领克中心” Evidence 未进入 prompt。三模型均未满足完整安全 contract，不能将其作为换模型失败的单一证据。

本轮不改变 retrieval、ranking 或 context selection。

## 17. Other Generation Cases

`epb_auto_subsection_answer_001` 中，M0 在正确核心结论后扩展 P 挡、手动 EPB 和 START/STOP 程序；M1/M2 只回答“静止并熄火后自动启用 EPB”，显示更好的 question-scope discipline。该改善来自模型行为，不是 prompt scope intervention。

## 18. Efficiency Observation

| Model | Average elapsed/case | Median elapsed/case | Relative avg vs M0 | Size |
| --- | ---: | ---: | ---: | ---: |
| M0 qwen2.5:7b | 9.0153s | 8.1255s | 1.00x | 4.7 GB |
| M1 qwen3.5:9b | 15.5973s | 16.8093s | 1.73x | 6.6 GB |
| M2 gemma3:12b | 17.9882s | 15.8765s | 2.00x | 8.1 GB |

这些是单次本地离线运行观测，包含 retrieval 和 generation，不是 production latency benchmark，也不是 p50/p95。M1 比 M0 多约 40% 模型文件体积，平均 elapsed 多约 73%；M2 的体积和平均 elapsed 均进一步增加。

## 19. Quality vs Deployment Tradeoff

- M0 部署成本最低，但两个高置信 generation condition failures 都保留，已构成 Resume-Ready answer-quality 瓶颈证据。
- M1 同时修复两个 target，并改善 EPB AUTO answer scope；相较 M2 更小、更快，normal/fallback 表达更清晰。
- M2 的主要质量收益与 M1 接近，但资源成本更高，且没有证明足以抵消额外 1.5 GB 模型体积和更长平均 elapsed 的独有收益。
- M1/M2 各有一条裸 Evidence ID 输出，说明模型升级不能替代后续独立的输出契约审查。

## 20. Final Model Recommendation

**RECOMMENDED_MODEL = `qwen3.5:9b`**。

理由：

1. 两个 primary model-capability targets 均实质改善；
2. proposed 7/7 regression guards 保持 Full Pass；
3. 没有新增 guard safety regression 或 hard-negative hallucination；
4. 与 M2 的 proposed quality 基本持平，但本地体积更小、平均 elapsed 更低；
5. 明确的 `think=false` 适配可审计、可测试且不修改 prompt semantics。

最终人工选型已确认 `ACCEPT`。Post-selection integration 将 production 默认模型切换为 `qwen3.5:9b`，并将 `think=false` 与既有 `temperature=0.0`、`seed=42`、`stream=false` 一起显式固化。

## 21. Known Limitations

- 仅 12 条单手册 dev diagnostic cases，不是 production accuracy benchmark。
- 每模型仅一次 12-case full run；另对选定的 M1 完成 4 cases x 3 runs 稳定性验证，但该验证不覆盖全部 12 cases，也不证明 M2 的跨次稳定性。
- M1 使用显式 `think=false`，M0/M2 使用 unset；这是建立 direct-answer comparability 的必要模型级差异。
- Ollama 模型 template 和继承 sampler defaults 不同，application-level 相同参数不代表内部生成语义完全相同。
- 最终人工选型已确认；本报告中的逐项 proposed rubric 仍不应冒充新的 final case-level adjudication。
- 单次 elapsed 不是正式 latency、吞吐或内存 benchmark。
- 自动 internal-reference proxy 不识别裸 `E1`，人工审阅发现 M1/M2 各一条此类泄漏。
- 两条 case 受 Prompt Evidence availability 限制，不能用于纯模型能力归因。

## 22. Implementation Boundary

为支持本实验做了最小基础设施修改：

- evaluator 支持 run-local `--model` 覆盖；
- evaluator 支持 run-local `--think true|false`；
- Ollama payload 仅在设置显式非空时发送顶层 `think`；
- artifact 记录 `generation_think` 及来源；
- production 默认已集成为 `qwen3.5:9b`，`OLLAMA_THINK=false`；run-local `--model` / `--think` override 保持可用。
- selected-model stability artifact：`reports/evaluation/v4_7_selected_model_generation_stability.json` 与对应 Markdown。

未修改 retrieval、rerank、parser、splitter、embedding、context selection、prompt、sanitizer、dataset 或 evaluation semantics。

## 23. Resume-Ready Impact

**ANSWER_MODEL_SELECTION_COMPLETE = YES**。最终人工决策为 `ACCEPT`，`qwen3.5:9b` 已完成 post-selection integration。选定模型在当前环境完成 4 cases x 3 runs 验证，Prompt Evidence identity/order/text、raw answer 和 final answer 均 exact match。

## 24. Global Project Information Sync Audit

| Surface | Decision | Reason |
| --- | --- | --- |
| README.md | UPDATE_REQUIRED | 同步已确认的稳定默认模型、显式 think 配置和下一阶段 |
| AGENTS.md | UPDATE_REQUIRED | 同步 V4.7 完成状态和 V4.8 Final System Evaluation 边界 |
| docs/evaluation.md | UPDATE_REQUIRED | 记录选型依据、稳定性边界和下一阶段 |
| `.env.example` | UPDATE_REQUIRED | 稳定默认改为 `qwen3.5:9b`、`OLLAMA_THINK=false` |
| Tests | UPDATE_REQUIRED | 覆盖 model/think run-local override 和 payload conditional field |
| Frozen V4.4/V4.5/V4.6 artifacts | NO_UPDATE_NEEDED | 历史结果不得覆盖或重解释 |

## 25. Decision Flags

- `PROMPT_EVIDENCE_INVARIANT = YES`
- `MODEL_COMPARISON_VALID = YES`
- `RECOMMENDED_MODEL = qwen3.5:9b`
- `KEEP_CURRENT_MODEL = NO`
- `ANSWER_MODEL_SELECTION_COMPLETE = YES`
- `FINAL_HUMAN_MODEL_SELECTION_DECISION = ACCEPT`
- `PRODUCTION_DEFAULT_MODEL_CHANGED = YES`
- `V4_7_PRODUCTION_DEFAULT_INTEGRATED = YES`
- `SELECTED_MODEL_REPEATED_RUN_STABILITY_VERIFIED = YES`
- `READY_FOR_FINAL_SYSTEM_EVALUATION = YES`

## 26. Next Step

V4.7 post-selection integration 已完成，建议在审阅 diff 和 stability artifacts 后精确提交。下一阶段是 V4.8 Final System Evaluation；本轮尚未启动该阶段。
