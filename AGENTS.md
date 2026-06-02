# AGENTS.md

## 1. 项目角色定位

本项目是一个面向汽车用户手册的本地化 RAG 系统。目标不是简单文档问答，而是构建具有工程质量和技术亮点的智能用车助手。项目后续会逐步支持：

- PDF 文档解析
- 汽车手册结构化 chunk
- 本地 embedding
- Chroma 向量检索
- 本地大模型问答
- 引用溯源
- 安全回答策略
- 检索评估
- 前端展示
- 工程化部署

当前项目已经进入 V3.x 迭代阶段，不再是从零搭建最小 RAG 闭环。当前阶段重点不是继续堆功能，而是提升：

- 可诊断性；
- 可评估性；
- 可维护性；
- 检索链路稳定性；
- 架构边界清晰度。

当前状态：

- V1 已完成最小 RAG 闭环，包括文档导入、文本切分、向量索引、检索、基于上下文回答和引用返回。
- V2 已完成汽车用户手册增强，包括 manual-aware chunking、metadata-aware context selection、基础引用质量优化和结构化日志。
- V3.0 已完成 Hybrid Retrieval 的基础实现，包括 BM25 sparse retrieval、dense retrieval 和 RRF fusion，并支持 `dense` / `bm25` / `hybrid` 三种 `retrieval_mode`。
- V3.0.1 已完成 index hygiene、TOC/noise filtering、`inspect_chunks`、conservative BM25 query filtering、content-level dedup 和 debug retrieval 增强。
- V3.0.2 已完成 evaluation dataset、evaluation runner 和基础 retrieval metrics。
- V3.0.3 已完成 cross-mode diagnostics。
- V3.1 已完成可关闭的本地 cross-encoder rerank baseline 和 rerank on/off comparison。
- V3.2 已将评测集扩展并清洗为 69 条 text-only dev cases，并完成 hybrid baseline 与 `BAAI/bge-reranker-base` 的复核。rerank 在当前 dev set 上明显改善 top-1 evidence ranking，但带来约 1.81x latency cost，因此 `ENABLE_RERANK=false` 仍为默认配置。
- 当前重点是继续 review failure cases、latency 和模块边界。不要在缺少更广泛评测依据时默认开启 rerank、引入 query rewrite 或继续叠加规则。

## 2. AI 编程助手工作原则

AI coding agent 在修改代码时必须遵守：

- 不要一次性实现过多功能。
- 每次任务只完成当前版本目标。
- 不要随意改变既有目录结构。
- 不要删除已有模块，除非明确说明原因。
- 不要硬编码模型名称、文件路径、API 地址等配置。
- 优先通过 config.py 和 .env 管理配置。
- 所有新增模块应保持职责单一。
- 所有复杂逻辑应有必要注释。
- 如果发现需求不明确，应先在输出中说明假设，而不是盲目实现。
- 生成代码后应说明修改了哪些文件、如何运行、如何测试。
- 优先修复通用工程问题，不围绕少量样例过拟合。
- 先保证可诊断，再做效果优化。
- 先建立评测，再做高级检索优化。
- 每个新增规则必须可解释、可 debug、可评估。
- 当系统变复杂时，应考虑消融实验和删减无效模块，而不是继续叠加补丁。

## 3. 项目架构约束

项目采用以下分层：

- app/api：FastAPI 路由层
- app/core：配置、日志、异常等基础设施
- app/data：文档加载、清洗、切分、数据模型
- app/rag：embedding、LLM、retriever、prompt、chain
- frontend：前端展示
- scripts：命令行脚本
- tests：测试代码
- data/raw：原始用户手册文件，本目录不提交 Git
- data/processed：处理中间结果，本目录不提交 Git
- data/chroma：本地向量库文件，本目录不提交 Git

V3.x 阶段必须进一步保持以下工程边界，避免逻辑散落和补丁化。

### 3.1 数据与 Chunk Hygiene 层

职责：

- TOC 检测；
- noise chunk 检测；
- 目录残片过滤；
- 前言泛说明过滤；
- content-level dedup；
- chunk metadata 质量检查。

约束：

- 这类逻辑应集中在 `chunk_filters` 或 ingestion / retrieval hygiene 相关模块中。
- 不应把 TOC/noise 判断散落在 QAChain、prompt 或 CLI 输出逻辑里。
- 过滤规则必须返回可解释的 `filter_reason` 或等价 debug metadata。

### 3.2 Retrieval 层

职责：

- dense retrieval；
- BM25 retrieval；
- hybrid retrieval；
- RRF fusion。

约束：

- retrieval 代码不应包含针对具体测试题的特殊规则。
- retrieval 代码不应硬编码页码、章节或答案。
- retrieval 只处理检索和融合，不负责生成答案。
- dense、BM25、hybrid 三种模式必须保持可独立调试。

### 3.3 Context Selection 层

职责：

- 从候选 chunk 中选择最终上下文；
- 控制上下文长度；
- 去重；
- 保留 citation metadata；
- 保守使用 metadata-aware ordering。

约束：

- 不要把 context selection 写成大量业务 if-else。
- 不要为了单个样例不断叠加 bonus / penalty。
- selection 的规则必须可解释、可 debug。
- context selection 不能替代 retrieval，也不能用来掩盖索引污染。

### 3.4 Generation 层

职责：

- prompt 构造；
- 回答格式；
- 禁止暴露内部编号；
- 基于上下文回答。

约束：

- 不要用 prompt 掩盖 retrieval 失败。
- 不要通过 prompt 编造上下文中没有的内容。
- 列表类问题可以要求尽量覆盖相关项目符号，但不能要求逐字复制或无根据扩写。
- citations 应由系统字段返回，不要求模型在正文中编造引用编号。

### 3.5 Diagnostics / Evaluation 层

职责：

- `inspect_chunks`；
- debug retrieval；
- evaluation dataset；
- evaluation runner；
- 指标计算；
- 日志可观测性。

约束：

- 诊断工具不应污染主链路。
- debug 字段应服务定位问题，而不是替代评测。
- evaluation 不应只依赖少量人工观察样例。
- 后续检索优化必须能通过 evaluation runner 做量化比较。

## 3.6 修改优先级

后续开发优先级如下：

1. 正确性和可复现性；
2. 索引卫生和候选上下文清洁度；
3. 日志、debug 和可诊断性；
4. 评测集、自动评测和消融实验；
5. 检索质量优化；
6. rerank、query rewrite、agent workflow 等高级功能。

当前已经具备 evaluation dataset 和 evaluation runner。后续引入复杂高级功能前，必须先通过现有评测体系和 failure analysis 证明必要性，并保留可关闭、可回滚路径。

## 3.7 新规则 / 新功能准入标准

任何新增 filter、penalty、bonus、query rule、prompt instruction、metadata selection rule 之前，必须回答以下问题：

1. 它解决的通用问题是什么？
2. 它属于系统哪一层？
3. 它是否可通过日志或 metadata debug？
4. 它是否能在后续 evaluation 中验证？
5. 它是否会显著增加复杂度？
6. 它是否可以配置化或关闭？
7. 它是否可能误伤其他问题类型？
8. 它是否只是为了修复 1 到 2 个样例？

如果一个规则只改善少数样例、缺乏通用解释、难以 debug 或难以评估，应避免加入主链路。

## 4. 汽车用户手册领域约束

本项目处理的是汽车用户手册，不是普通文本。开发时必须特别注意：

- 手册中的“警告”“注意”“说明”具有不同安全含义。
- “警告”通常涉及人身伤害或生命危险，不能在切分、摘要、回答时丢失。
- “注意”通常涉及车辆损坏风险，需要保留。
- “说明”通常是辅助解释或使用提示。
- 操作步骤必须尽量保持完整，不能随意切断。
- 章节标题、页码、功能名称、系统名称应尽量作为 metadata 保存。
- 对安全相关问题，应优先召回包含 warning/caution 类型的 chunk。
- 回答中不能编造车辆功能。
- 如果检索不到依据，应明确说明没有在手册中找到可靠依据。

## 5. RAG 回答原则

后续实现问答时，必须遵守：

- 回答必须基于检索到的上下文。
- 尽量返回引用来源，包括 source_file、page、chapter、section。
- 不允许用模型常识替代手册内容。
- 不允许编造页码、章节或引用。
- 对涉及驾驶安全、高压系统、充电、制动、儿童安全、气囊、故障警告灯的问题，回答应更加保守。
- 对高风险问题，必要时提示用户联系 Lynk & Co 领克中心或专业维修人员。

## 6. 本地模型约束

项目优先支持本地模型：

- LLM 默认通过 Ollama 调用。
- Embedding 默认支持本地 embedding 模型。
- LLM 和 Embedding 都必须设计成可替换接口。
- 不要把某个模型写死在业务代码中。
- 所有模型名称、base_url、超时时间等都应通过配置读取。

## 7. 代码质量要求

要求：

- Python 代码应清晰、类型标注尽量完整。
- Pydantic 模型字段要语义明确。
- API 输入输出结构要稳定。
- 错误处理不能直接吞掉异常。
- 日志应记录关键流程，例如 ingest、chunk 数量、query、retrieved chunks 数量等。
- 不要在业务代码中 print 调试信息，优先使用 logger。
- 测试代码应放在 tests/ 目录。
- 脚本代码应放在 scripts/ 目录。
- Python 代码应模块化，函数职责单一。
- 重要规则必须有清晰命名。
- 复杂过滤、排序、去重逻辑必须可 debug。
- 日志应包含关键阶段字段，例如 `stage`、`retrieval_mode`、`filter_reason`、`candidate_count` 等。
- 不要把大量业务规则堆在一个函数中。
- 不要让主链路依赖调试脚本。
- 不要破坏 FastAPI、CLI、Streamlit 主流程。

依赖约束：

- 不要引入 LangChain。
- 不要引入 LlamaIndex。
- 不要引入大型 NLP 依赖。
- 不要引入复杂服务依赖。
- 除非明确要求，否则优先使用项目已有依赖和轻量工具。

## 8. Git 与提交规范

建议使用清晰的 commit message，例如：

- init project skeleton
- add pdf loader
- implement basic chunk splitter
- add chroma retriever
- implement ollama llm client
- add streamlit demo
- add retrieval evaluation script
- improve hybrid retrieval index hygiene
- add chunk inspection diagnostics
- refactor context selection pipeline

不要把以下内容提交到 Git：

- .env
- 原始 PDF 手册
- 本地 Chroma 数据库
- processed 中间文件
- data/processed/*.pkl
- logs/
- .venv/
- __pycache__
- 大模型权重文件
- .idea/
- 本地 IDE 配置
- 临时调试输出文件

提交前必须：

1. 运行语法检查：

   ```bash
   python -m compileall app frontend scripts
   ```

2. 如果修改了 indexing / retrieval / filtering / tokenizer / chunking 相关逻辑，必须重新构建索引。
3. 至少运行 smoke tests，确认系统没有明显崩溃。
4. 检查 `git status`，确认没有提交原始 PDF、索引、日志、本地环境或 IDE 文件。

Commit message 应描述真实改动，避免无意义提交信息，例如：

- fix
- update
- test
- final

## 9. 当前版本路线

项目迭代路线：

- V0：项目初始化
- V1：最小 RAG 闭环
- V2：汽车手册结构化解析、manual-aware chunking、metadata-aware context selection 和基础日志
- V3.0：Hybrid Retrieval 基础实现，包括 dense retrieval、BM25 sparse retrieval 和 RRF fusion
- V3.0.1：Index hygiene 与 diagnostics，包括 TOC/noise filtering、inspect_chunks、conservative BM25 query filtering、content-level dedup 和 debug retrieval 增强
- V3.0.2：Evaluation dataset、evaluation runner 和基础 retrieval metrics
- V3.0.3：Cross-mode diagnostics 和 case-level failure analysis
- V3.1：可关闭的本地 cross-encoder rerank baseline 和 rerank on/off comparison
- V3.2：将评测集扩展并清洗为 69 条 text-only dev cases，复核 rerank 排序收益与 latency cost；rerank 继续作为 optional enhancement，默认关闭
- V3.3：基于更广泛评测继续做 failure review、latency review、消融实验、模块裁剪和架构收敛
- V4：安全回答策略强化、引用溯源强化和前端展示
- V5：工程化打磨、部署、文档和简历包装

## 10. 反过拟合原则

当前项目已经进入 69 条 text-only dev evaluation set、evaluation runner 和 rerank comparison 阶段。反过拟合原则适用于所有 dev cases、failure cases、rerank improved / regressed cases 和人工审查样例，不再只针对早期 smoke tests。

必须遵守：

- 不得为了单个 case 写死页码、section、chunk_id、答案或 query-specific if-else。
- 不得根据单个 failed case 直接新增 retrieval rule、rerank rule、bonus / penalty 或 prompt 特例。
- 不得为了提升 dev set 指标而删除困难样例、放宽 expected evidence、扩大 `acceptable_sections` 或修改 evidence。
- 不得把当前 69 条 dev cases 当成 final benchmark。
- 不得把 visual-dependent 问题混入当前 text-only retrieval / rerank 主评测。
- 不得用 prompt 弥补 retrieval、chunking、metadata 或 evidence 标注问题。
- 所有新增规则必须解决一类通用问题，并通过日志、debug metadata 或 evaluation runner 验证。
- 宽泛问题和具体步骤问题必须区分意图，例如“如何正确使用安全带”和“如何系紧安全带”不是完全等价的问题。

早期四个 smoke tests 仍可保留为回归检查样例：

1. 如何正确使用安全带？
2. 胎压报警后应该怎么办？
3. 车辆涉水驾驶后需要检查什么？
4. 充电时有哪些安全注意事项？

这些 smoke tests 不是训练集，不是唯一优化目标，也不能代表系统整体效果。任何新增规则都必须解决一类通用问题，而不是只提升一两个样例的表现。

## 11. Smoke Tests 定位

Smoke tests 用于快速发现明显崩溃或重大回归。

必须明确：

- 通过 smoke tests 只说明主链路基本可运行，不说明系统效果可靠。
- smoke tests 不应替代 evaluation runner。
- smoke tests 不应作为 rerank、query rewrite 或 chunking 优化的唯一依据。
- 某个 smoke test 失败时，应先查看 retrieval debug、chunk evidence、metadata 和 evaluation report，而不是立即新增规则。
- 宽泛问题和具体步骤问题必须区分意图，例如“如何正确使用安全带”和“如何系紧安全带”不是完全等价问题。

当前效果判断优先级：

1. evaluation dataset 的整体指标；
2. rerank / no-rerank comparison；
3. case-level improved / regressed / unchanged 分析；
4. failure case review；
5. smoke tests 和人工 spot check。

## 12. 评测路线

当前 V3.2 阶段已经建立并清洗了 69 条 text-only dev evaluation set。该评测集用于开发阶段的 retrieval、rerank、chunking、metadata 和 failure analysis。它不是 final benchmark。

当前系统是 text-only RAG。核心答案依赖图标、按钮示意图、编号图例或视觉版面的问题，应删除、改写或单独标注为未来多模态扩展问题，不纳入当前 retrieval / rerank 主评测。

每条 eval case 必须包含：

- `id`
- `question`
- `category`
- `intent_type`
- `expected_pages`
- `expected_sections`
- `acceptable_sections`
- `must_contain_terms`
- `answer_must_cover`
- `forbidden_content`
- `evidence`

评测数据要求：

- `category` 表示问题主任务类型，`intent_type` 表示用户意图的细粒度形式。
- evidence 必须可追溯到 indexed chunk，quote 应能在 chunk 原文中匹配。
- `answer_must_cover` 不得超出 evidence quote 能支撑的范围。
- 宽泛问题和具体步骤问题必须分开标注。
- `expected_sections` 不应过窄，必要时使用 `acceptable_sections` 表达合理相关章节。
- section metadata 可能存在缺失或错位，评测时不能只看 `section_hit`，应结合 page、quote、chunk_id 和 `must_contain_terms`。
- visual-dependent cases 不纳入当前 text-only 主评测。
- 不能用单一标准答案误判合理回答。

当前核心 retrieval / rerank 指标：

- `evidence_hit@1` / `evidence_hit@3` / `evidence_hit@5`
- `page_hit@1`
- `MRR`
- `average_first_hit_rank`
- `final_context_hit`
- noise rate
- duplicate rate
- improved / regressed / unchanged cases
- `lost_top1_hit`
- `evidence_hit@5_regressions`
- latency cost

V3.2 rerank comparison 结论：

- 在 69 条 text-only dev cases 上，hybrid + `BAAI/bge-reranker-base` 相比 hybrid baseline 明显提升 top-1 evidence ranking。
- `evidence_hit@1` 从 `0.7681` 提升到 `0.9130`。
- `MRR` 从 `0.8792` 提升到 `0.9541`。
- `evidence_hit@3` 和 `evidence_hit@5` 均保持 `1.0000`。
- 没有 `lost_top1_hit`，也没有 `evidence_hit@5` regression。
- rerank 带来约 `1.81x` latency cost。
- rerank 保留为 optional enhancement，`ENABLE_RERANK=false` 仍为默认配置。

train / dev / test 原则：

- train set 用于开发观察。
- 当前 69 条数据是 dev set，用于方案比较和 failure analysis。
- 未来如建立 test set，必须冻结。
- 不得根据 test set 的具体失败样例直接调规则。
- 避免把评测集变成新的训练集。

后续评测路线：

1. 对 regressed cases 和 unchanged non-top1 cases 做 failure case review。
2. 区分 retrieval failure、rerank failure、chunk boundary 问题、section metadata 问题和 visual-dependent 问题。
3. 在 failure review 之前，不引入 query rewrite。
4. 在更大范围评测、参数对照和 latency review 完成前，不默认开启 rerank。
5. 后续可对比 `rerank_top_n=10` 与 `rerank_top_n=20`。
6. 后续可对比 `BAAI/bge-reranker-base` 与 `BAAI/bge-reranker-v2-m3`。
7. 如果 rerank 进入用户请求链路，必须补充更细粒度 latency metrics。
8. 如果继续扩充评测集，只应补充能增加覆盖面的 text-only cases，不为凑数量添加低质量样例。
9. 后续 answer-level evaluation 可考虑 citation correctness、groundedness、completeness 和 forbidden content rate。

所有后续 rerank、query rewrite、chunk 优化、metadata selection 调整，都必须通过 evaluation runner 做量化验证，并结合人工 failure analysis 解释结果。

## 13. 明确禁止事项

禁止：

1. 为单个测试问题硬编码规则；
2. 为单个测试问题硬编码页码；
3. 为单个测试问题硬编码 section；
4. 为单个测试问题硬编码答案；
5. 在缺少 evaluation runner 量化依据和 failure analysis 时默认开启或扩大复杂 rerank；
6. 在 failure review 之前引入 query rewrite；
7. 无限制增加 penalty / bonus / if-else；
8. 用 prompt 掩盖 retrieval 失败；
9. 为了提高少数样例效果牺牲系统可维护性；
10. 提交生成的索引文件、日志、原始 PDF 或本地环境文件。

## 14. 对 Codex 的特别要求

每次 Codex 修改项目时，输出必须包含：

1. 本次任务目标
2. 修改的文件列表
3. 核心实现说明
4. 如何运行
5. 如何测试
6. 是否有未完成事项
7. 下一步建议

并且不要在没有明确要求的情况下跨版本实现后续功能。
