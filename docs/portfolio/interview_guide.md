# Auto Manual RAG 面试讲解指南

这份材料用于理解和讲清项目，不建议逐字背诵。所有数字和结论以 [冻结技术事实](technical_facts.md) 及对应评测报告为准。

## 30 秒项目介绍

我做了一个面向汽车用户手册的本地可追溯问答应用。它先恢复 PDF 的章节和小节结构，再用 Dense、BM25 和 RRF 做混合检索，通过有限 Evidence 驱动本地模型回答并返回页码引用。除了 FastAPI、Streamlit 和 CLI，我还建立了检索、答案和可复现性评测，用受控实验而不是个别样例调参来决定系统改动。

## 3 分钟项目介绍

汽车用户手册不是把 PDF 按固定长度切开就能可靠问答的材料。目录、页眉页脚、图例、跨页列表会污染索引；“警告”“注意”“说明”具有不同安全含义；相邻小节又经常共享“制动”“充电”“安全带”这类词，所以纯语义相似度容易命中同主题但不直接回答问题的内容。

数据侧，我实现了 manual-aware parser 和 splitter，从 PDF 文本中恢复 chapter、section、subsection 和 heading path，同时保留 page、content type、risk level 与 source pages。section 主要保存在 metadata，subsection 会进入 chunk text，以兼顾结构可追溯性和小节语义召回。

检索侧使用 Chroma Dense 和 BM25 双路召回，通过 RRF 融合排名。BM25 使用轻量中文字符 n-gram tokenizer；索引和查询链路统一做 TOC/noise filtering 与 exact content dedup。融合后的候选再经过 metadata-aware context selection，最终最多保留 5 条、6000 字符的 Evidence，不让 Prompt 随候选数量无限增长。

生成侧使用 Ollama `qwen3.5:9b`。Prompt 明确证据边界、冲突和条件差异；系统记录 Exact Prompt Evidence、raw answer、final answer 和 citations，因此能区分问题出在 retrieval、上下文可用性还是模型使用证据的方式。

工程上，我没有只围绕几个问题调规则。我把 retrieval benchmark 校准到当前 chunk strategy，支持 multi-gold 和 excluded cases；又建立 12-case answer diagnostic set、人工 rubric 和可复现配置。一次 Condition Preservation Prompt 实验在 Evidence 不变时没有修复目标问题，因此被 REJECT、没有进入稳定分支。随后三模型比较保持 12/12 Prompt Evidence 完全一致，`qwen3.5:9b` 与 `gemma3:12b` 都改善关键条件处理，但前者更小、离线 elapsed 更低，因此选为默认模型。

最终稳定 hybrid no-rerank 在 68 条 active retrieval dev queries 上为 Hit@5 `0.9706`、MRR `0.7922`。这些是单手册 dev benchmark 指标，不是系统准确率；项目也明确保留多手册、多模态、安全证据覆盖和正式 latency benchmark 等限制。

## 10 分钟技术 Walkthrough

### 1. Problem definition

- **What**：把汽车用户手册转为带证据引用的本地问答应用。
- **Why**：手册结构复杂、安全要求敏感，通用 PDF QA 容易检索错小节或丢条件。
- **Trade-off**：聚焦单手册 text-only 场景，先保证可追溯和可评估，不承诺跨车型泛化。

### 2. Data ingestion

- **What**：`PDFLoader -> clean_text -> ManualStructureParser -> ManualStructureSplitter -> Chroma/BM25`。
- **Why**：让两类索引来自同一批结构化 chunks，避免检索语义漂移。
- **Trade-off**：原始 PDF、索引和模型不提交，fresh clone 需要用户提供合法手册并 ingest。

### 3. Manual-aware parsing

- **What**：状态机式维护 chapter、section、subsection 和文本 buffer，识别标题、安全 marker、列表与正文。
- **Why**：固定长度切分不知道标题归属，也容易把警告和操作步骤拆开。
- **Trade-off**：规则对当前手册做保守校准；迁移到新手册必须抽查 metadata，不能假设通用。

### 4. Chunking and metadata

- **What**：按 ManualBlock 切分，尽量在列表、警告和句子边界处分块，保留 hierarchy、page、source pages、content type 和 risk level。
- **Why**：retrieval、citation、debug 和 evaluation 都需要同一结构事实。
- **Trade-off**：section 不重复写进正文以减少噪声；subsection 写入正文以增强细粒度召回。

### 5. Dense retrieval

- **What**：使用 `BAAI/bge-small-zh-v1.5` 生成向量，Chroma 按 cosine distance 检索。
- **Why**：覆盖用户问法与手册表达不完全一致的语义匹配。
- **Trade-off**：相近小节语义过于接近时，Dense 的 top-1 区分能力有限。

### 6. BM25

- **What**：基于 char unigram/n-gram 与英文数字 token 的 BM25Okapi sparse retrieval。
- **Why**：补足故障码、系统名、按钮名和精确操作短语等 lexical signal。
- **Trade-off**：不引入大型中文分词依赖；泛词需要保守过滤，不能按测试题写词表。

### 7. RRF

- **What**：按 `1 / (RRF_K + rank)` 累加 Dense/BM25 排名，当前 `RRF_K=60`。
- **Why**：两路 score 尺度不同，RRF 只依赖 rank，简单且可解释。
- **Trade-off**：它能融合召回，但不能理解互补 Evidence 是否必须同时出现。

### 8. Filtering and dedup

- **What**：在索引、检索、融合和最终上下文阶段识别 TOC/noise，按 normalized exact text 去重。
- **Why**：目录残片、前言泛说明和重复警告会占据 top-k 与 Prompt 预算。
- **Trade-off**：规则保持保守，避免把真实短步骤或安全警告误删；不做复杂近似相似度去重。

### 9. Context selection

- **What**：对候选增加可解释 metadata score，按问题意图和 section/content type 做轻量选择。
- **Why**：融合排名之后仍需要把有限 Prompt 预算给更直接的证据。
- **Trade-off**：它不是第二套 retrieval，不应堆叠 case-specific bonus；仍可能遗漏互补 Evidence。

### 10. Grounded generation

- **What**：Evidence 带 E1-E5 边界、page/hierarchy/content type，Prompt 要求仅依据 Evidence、保留安全条件、区分条件差异与真正冲突。
- **Why**：模型要知道哪些文字是证据，以及哪些条件不能被泛化。
- **Trade-off**：Prompt 不能补回没有进入上下文的 Evidence，也不能保证模型绝不越界。

### 11. Citations

- **What**：系统代码根据最终 Prompt contexts 构造 source file、page、section、subsection 和 relevant quote。
- **Why**：引用不依赖模型编写页码，Prompt 和 citations 使用同一组 chunks。
- **Trade-off**：quote 是面向用户的摘录，不等于模型实际看到的全部 Evidence。

### 12. Evaluation

- **What**：69-record retrieval benchmark、12-case answer diagnostic set、自定义 metrics、benchmark validation 和 human rubric。
- **Why**：把“看起来答得好”转为可复现、可比较、可定位的工程证据。
- **Trade-off**：都是单手册 dev data，不能冒充外部 test 或 production accuracy。

### 13. Reproducibility

- **What**：记录 dataset hash、semantics、Git identity、model digest、Ollama version、Prompt hash、temperature、seed、think 与 Exact Prompt Evidence。
- **Why**：比较结果前先证明变量确实被冻结。
- **Trade-off**：固定参数只在当前环境验证，不能保证跨硬件或 runtime 版本一致。

### 14. Failure-driven optimization

- **What**：从人工 failure taxonomy 建立 hypothesis、control/treatment、guard cases 和 ACCEPT/REJECT criteria。
- **Why**：避免看到一个失败就继续加 Prompt 规则。
- **Trade-off**：实验流程更慢，但能拒绝无效改动并保留负结果。

### 15. Model selection

- **What**：固定 RAG pipeline，对 `qwen2.5:7b`、`qwen3.5:9b`、`gemma3:12b` 做 12-case 比较。
- **Why**：V4.6 Prompt 干预无效后，需要验证是否是模型使用 Evidence 的能力瓶颈。
- **Trade-off**：`qwen3.5:9b` 比旧模型慢，但比质量相近的 12B 模型更小、更快。

### 16. Limitations

- **What**：单手册、text-only、小型 answer diagnostic set、互补/安全 Evidence 可用性和非正式 latency。
- **Why**：这些边界决定结果能说明什么、不能说明什么。
- **Trade-off**：项目选择在证据足够时冻结，而不是为了功能数量继续扩张。

## 核心工程决策

1. **Hybrid 而非单路检索**：语义召回与精确术语互补。
2. **RRF 而非 score normalization**：避免人为对齐 Dense 与 BM25 score 尺度。
3. **Rerank 保持可选**：dev 排序收益明确，但本地离线成本更高，且尚无正式在线 latency 数据。
4. **Evidence budget 写在代码层**：最终 contexts 与 citations 使用同一集合，避免 Prompt 静默丢 Evidence。
5. **评测与生产链路分层**：debug/report 不改变用户查询行为。
6. **失败实验不合并**：V4.6 treatment 无目标收益，稳定 Prompt 保持不变。
7. **模型选择用 causal isolation**：12/12 Prompt Evidence invariant 后才比较回答。

## 三个关键工程故事

### Story 1：Retrieval benchmark recalibration

**背景**：parser/chunk hierarchy 变化后，旧 gold chunk ID、边界和 metadata 可能不再对应当前 index。直接复跑会把 benchmark stale 当成 retrieval miss。

**行动**：逐 case 审计原始问题、手册事实和当前 chunks；引入 consistency validator；对等价且独立充分的 chunks 使用 multi-gold ANY_OF；将 text-only corpus 没有表格数值的 case 保留为 excluded，而不是伪造 gold 或删除历史。

**结果**：冻结为 69 records、68 active、1 excluded、99 gold evidence，validation issues 为 0。重要认识是 benchmark truth 也需要版本治理，指标变化不一定等于 production retrieval 变化。

### Story 2：Rejected Prompt experiment

**背景**：旧模型在 EPB 释放和遥控钥匙启动中丢失前提或把 fallback 泛化成普通流程。

**行动**：先建立 fixed-generation R0，只在 T1 加一条通用 Condition Preservation 规则；冻结 dataset、retrieval、context、model、temperature、seed 和 Prompt Evidence，预先定义两个 target 与七个 regression guards。

**结果**：两个目标错误都没有消除，因果隔离成立，因此结论为 REJECT；Prompt delta 被移除，报告保留。工程价值在于阻止无效 Prompt hill-climbing 进入稳定系统。

### Story 3：Answer model selection

**背景**：Prompt 单规则干预无效，需要判断 `qwen2.5:7b` 是否是 Evidence reasoning 的能力瓶颈。

**行动**：保持 12/12 Prompt Evidence identity/order/text 完全一致，对比 `qwen2.5:7b`、`qwen3.5:9b`、`gemma3:12b`。重点查看 EPB prerequisite 和 normal/fallback 条件，而不是只看 lexical proxy。

**结果**：旧模型把仅在遥控钥匙电量低或未识别时使用的杯托 fallback 提升为普通启动第一步；两个新模型都正确保留条件，并补齐 EPB AUTO prerequisite。`qwen3.5:9b` 与 12B 模型质量接近，但约 6.6 GB、平均离线 elapsed 约 15.60 秒，低于后者 8.1 GB、17.99 秒，因此被选中。

## 高频面试问题

### 1. 为什么不用纯 Dense Retrieval？

**Short Answer**：手册相邻小节语义很像，Dense 擅长语义召回但容易把“功能说明”和“具体操作”混在一起；BM25 能补充系统名、按钮、故障码和精确短语信号。

**Deep Dive**：本项目没有让 BM25 替代 Dense，而是让两路独立召回后用 RRF 融合。稳定配置仍有 Hit@1 低于 Hit@5 的现象，说明召回基本到位但 top-1 区分仍有空间。

### 2. BM25 在这里解决什么问题？

**Short Answer**：它提高“EPB”“START/STOP”“ISOFIX”等术语以及具体操作短语的可见性，弥补 embedding 对近义章节的区分不足。

**Deep Dive**：中文 tokenizer 使用单字和 2-5 gram，加英文数字 token；query 端只保守降低泛词影响，并记录 coverage/penalty debug，不用面向评测题的固定词表。

### 3. 为什么使用 RRF？

**Short Answer**：Dense distance 和 BM25 score 不在同一尺度，RRF 直接融合排名，不需要设计脆弱的分数归一化。

### 4. RRF 是怎么工作的？

**Short Answer**：某 chunk 在每一路的第 `rank` 位贡献 `1/(k+rank)`，两路贡献相加后排序；本项目 `k=60`。两路都靠前的 chunk 会获得更高融合分。

### 5. 为什么最终 reranker 默认关闭？

**Short Answer**：`BAAI/bge-reranker-base` 将 Hit@1 从 0.6618 提升到 0.8676，但单次本地离线 elapsed 从约 21.11 秒增加到 42.96 秒。它被保留为可选高精度能力，默认系统选择较低成本的 no-rerank。

**Deep Dive**：这些 elapsed 不是 online p95，所以我不会声称线上延迟翻倍；默认决策还考虑架构复杂度和 Resume-Ready 本地部署成本。

### 6. Hit@1、Hit@3、Hit@5 是什么？

**Short Answer**：它们表示前 1、3、5 个结果中是否至少出现一个 gold Evidence。当前 stable hybrid no-rerank 为 0.6618、0.9265、0.9706。

### 7. MRR 是什么？

**Short Answer**：对每个问题取第一个正确 gold 的倒数排名，再对全部 active cases 求平均。它同时奖励命中和靠前排序，本项目稳定 MRR 为 0.7922。

### 8. 为什么 Hit@5 很高但 Hit@1 较低？

**Short Answer**：说明目标 Evidence 大多已经进入候选，但同主题小节、重复术语和条件相近内容会排在它前面，主要矛盾更接近 ranking 而不是完全召回失败。

### 9. multi-gold evaluation 是什么？

**Short Answer**：当前 corpus 中可能有多个独立、完整地支持同一事实的重复 chunks。benchmark 将它们都列为 gold，TopK 命中任意一个就成功，MRR 使用排名最高的那个。

### 10. 为什么 EPB case 暴露了 Hit@K 的局限？

**Short Answer**：有些问题需要“启用”和“释放”两条互补 Evidence。ANY_OF Hit@K 命中其中一条就成功，但并不代表回答所需证据齐全。

### 11. 为什么没有加 GoldEvidenceCoverage@K？

**Short Answer**：V3.5 已冻结现有 evaluator 语义，而数据集还没有系统区分 equivalent ANY_OF 与 complementary ALL_OF groups。直接增加指标会把两种 gold 关系混在一起，所以只记录为 future work。

### 12. manual-aware chunking 和固定长度 chunk 有什么区别？

**Short Answer**：前者先恢复章节和安全/步骤边界，再在 block 内切分；固定长度只按字符窗口处理，容易切断警告、列表或把标题归到错误正文。

### 13. heading_path 有什么作用？

**Short Answer**：它把 chapter、section、subsection 串成结构路径，用于 Prompt Evidence、debug、citation 和评测校验，让相同正文词汇有明确的手册位置。

### 14. 为什么 section heading 不进入 chunk text？

**Short Answer**：section 已作为稳定 metadata 保存，重复写入每个 chunk 会放大公共标题词、影响 BM25 和重复内容；更细粒度的 subsection 会 prepend 到正文，用于增强小节语义。

### 15. 如何防止目录或 TOC 污染 retrieval？

**Short Answer**：parser 初步跳过目录特征，BM25 build 前过滤 TOC/noise，Dense/BM25、fusion 和 final context 又做兜底过滤；每次过滤都有 stage 和 reason 便于诊断。

### 16. metadata-aware context selection 做了什么？

**Short Answer**：它在融合候选上结合问题关键词、意图和 chunk 的 section/content type/risk metadata 做轻量可解释排序，选择最终 Evidence。它不替代 retrieval，也不允许堆 case-specific 规则。

### 17. 为什么 context 有 max_contexts 和 max_chars？

**Short Answer**：防止候选增长导致 Prompt 膨胀和无关 Evidence 污染。QAChain 最终固定同一组 contexts 给 Prompt 和 citations，默认最多 5 条、6000 字符，并保持排序。

### 18. 什么是 Exact Prompt Evidence？

**Short Answer**：它是模型实际看到的每条 Evidence 快照，包括 ID、顺序、chunk ID、结构 metadata、正文和截断状态。它比只记录 retrieval candidates 更接近回答因果链。

### 19. 为什么 citation.quote 不能替代 Prompt Evidence 做人工评测？

**Short Answer**：quote 是回答后为用户提取的短摘录，可能只覆盖 chunk 的一部分；人工 groundedness 必须基于模型实际可见的完整 Evidence，否则会错误地把模型没看到的内容当作依据。

### 20. Groundedness、Correctness、Completeness 有什么区别？

**Short Answer**：Groundedness 看陈述是否有 Evidence；Correctness 看是否准确表达方向、状态和事实；Completeness 看是否覆盖问题要求的核心点。一个回答可以有依据但理解错，也可以正确但漏项。

### 21. 为什么 temperature=0 还需要 seed？

**Short Answer**：temperature=0 表达应用层的低随机采样意图，seed 进一步固定支持它的 runtime 随机路径。两者都显式记录能消除配置歧义，但仍不能保证跨硬件或版本一致。

### 22. 可复现性的边界是什么？

**Short Answer**：项目只证明当前硬件、Ollama 0.33.2、固定模型 digest、Prompt 和 generation config 下 4 cases x 3 runs 的 raw/final output 相同，不声称跨 backend、跨版本或跨机器 determinism。

### 23. V4.6 Prompt experiment 为什么被 REJECT？

**Short Answer**：只增加通用 Condition Preservation 规则后，两个预设 target 的错误都没有消失；虽然七个 guard 没退化，但实验没有目标收益，所以按预注册标准 REJECT，并移除 delta。

### 24. 为什么失败实验也有工程价值？

**Short Answer**：它证明了“继续加一句 Prompt”不是有效解决方案，阻止无效复杂度进入稳定系统；同时保留 hypothesis、冻结变量和结果，让下一步模型选型有依据。

### 25. 为什么从 qwen2.5:7b 换成 qwen3.5:9b？

**Short Answer**：在完全相同 Prompt Evidence 下，新模型修复了 EPB prerequisite omission 和遥控钥匙 normal/fallback 混淆，并保持七个 guard；相对质量接近的 `gemma3:12b`，它更小且本地 elapsed 更低。

### 26. 怎么证明是模型能力改善，而不是 retrieval 改善？

**Short Answer**：三个 model run 的 dataset、Prompt hash、retrieval/context config 都相同，而且 12/12 cases 的 Evidence identity、order、text exact match。主要独立变量只有 answer model 和模型必要的 direct-answer think 配置。

### 27. 为什么没有继续做 Query Rewrite？

**Short Answer**：冻结评测显示 no-rerank Hit@5 已达 0.9706，主要已知失败更集中在排序、互补 Evidence 和模型使用条件，而不是普遍 query recall。继续加 rewrite 会增加变量和调试成本，缺少高 ROI 证据。

### 28. 为什么没有做 embedding benchmark？

**Short Answer**：当前 BGE embedding 与 hybrid pipeline 已形成稳定 benchmark，现有证据没有证明 embedding 是 Resume-Ready blocker。项目优先闭合应用、评测和模型选型，而不是为了技术清单继续搜索模型。

### 29. 为什么不能说 10/12 等于 83.3% accuracy？

**Short Answer**：这是单手册 12-case dev diagnostic set 上的 PROPOSED human rubric Full Pass，不是冻结外部 test，更不是线上用户分布。直接叫 accuracy 会扩大数据规模、裁决状态和泛化范围。

### 30. 如果继续做，最优先改什么？

**Short Answer**：先扩展跨手册外部评测，并显式建模 complementary/safety-critical Evidence coverage；只有确认失败层后，再选择 context selection、embedding 或 query transformation。正式 latency 也需要独立做 warmup、重复运行和 p50/p95。

## 项目不足怎么回答

可以直接回答：

> 当前项目最大的限制是证据范围，而不是再缺一个高级 RAG 名词。检索 benchmark 只来自一本手册，answer diagnostic set 只有 12 条；纯文本 parser 不能恢复图片和复杂表格；互补 Evidence 和安全 Evidence 仍可能没有进入最终 Prompt；本地 elapsed 也不是生产 latency benchmark。下一步应先建立多手册外部 test、补充 complementary/safety coverage 指标和正式 latency 测量，再由失败证据决定是否做 retrieval 或 query transformation。

其他边界：

- fresh clone 命令已核对，但未在全新机器完成模型下载、合法手册准备和冻结 index 重建。
- `qwen3.5:9b` 偶尔可能输出裸 E1/E2；sanitizer 不全局删除，以免误伤真实故障码。
- parser 对当前手册结构做过保守校准，换手册必须重新检查 hierarchy 与 benchmark mapping。

## AI 辅助开发怎么回答

推荐回答：

> 项目开发中使用了 Codex 辅助代码生成、重复实现、测试补充和代码审查，但架构边界、评测合同、gold evidence 审计、实验独立变量和 ACCEPT/REJECT 决策需要我理解并确认。AI 生成的改动不会直接进入稳定分支，我会通过 unit tests、benchmark consistency validation、Exact Prompt Evidence、受控实验和 Git diff boundary 验证。面试中我可以从 parser、RRF、context assembly、QAChain 和 evaluator 解释输入输出、算法和取舍，而不是只展示生成结果。

### AI_ASSISTED_DEVELOPMENT_RISK_AREAS

项目作者在面试前必须亲自掌握：

1. `ManualStructureParser` 的状态与 flush 边界，尤其 section/subsection 的差异。
2. BM25 tokenizer、dynamic query coverage 和 soft penalty 的真实行为。
3. HybridRetriever 的 RRF、metadata merge、filter 与 dedup 顺序。
4. Context selection 与最终 5 contexts/6000 chars 的预算不变量。
5. QAChain 中 Prompt Evidence 与 citations 使用同一 contexts 的保证。
6. Hit@K、MRR、multi-gold ANY_OF、excluded case 和 benchmark validation。
7. Answer evaluator 的 deterministic proxy 与 human rubric 的边界。
8. V4.6 为什么 REJECT、V4.7 为什么能把改善归因于模型。
9. `temperature/seed/think` 的应用层含义和可复现性边界。
10. 项目没有实现的能力，特别是多模态、外部 test、正式 latency、Agent/MCP。

## Future Work

按当前证据排序：

1. 建立多手册、跨车型的外部 retrieval/answer test set。
2. 为 complementary Evidence 和 safety-critical Evidence 建立明确 coverage contract。
3. 对图片、按钮图标和复杂表格建立独立多模态 ingestion 路线。
4. 做带 warmup、重复运行和 p50/p95 的 latency benchmark。
5. 只有新的失败证据明确指向 retrieval/query 表达时，再评估 embedding 或 query transformation。

Agent、MCP 和 GraphRAG 不属于当前项目的自然延伸，应作为独立项目讨论。
