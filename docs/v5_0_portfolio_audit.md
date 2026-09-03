# V5.0-A Portfolio / README Audit

## 1. Executive Assessment

`auto_manual_rag` 已经具备一个完整垂直 AI 应用的技术核心：从汽车用户手册 PDF 导入、结构恢复、双路索引、混合检索、上下文整理，到本地模型回答、引用返回、API/UI/CLI 入口，以及 retrieval/answer evaluation、证据追踪和可复现生成。代码和冻结 artifact 足以证明它不是“PDF -> 向量库 -> LLM”的教程项目。

当前 Portfolio 的主要问题不在技术深度，而在信息架构和可体验性：README 仍是 572 行阶段性内部说明，评测和版本历史占比明显高于用户问题、应用工作流、Quick Start 和 Demo；仓库有 48 份已跟踪 evaluation reports，却没有报告索引、截图、示例问答或新用户可验证的完整路径。对 AI Application Engineer 招聘者而言，当前状态容易形成“评测体系很强，但产品/应用展示很弱”的印象。

V5.0-B 应优先把现有能力变得可理解、可运行、可展示，而不是新增 Agent、检索算法或模型实验。

## 2. Current Portfolio Readiness

### 2.1 Audit context

- Target role：AI Application Engineer / AI 应用开发工程师。
- Compatible roles：LLM Application Engineer、RAG Engineer、Agent Application Engineer、AI Backend Engineer。
- Current branch：`docs/v5.0-portfolio-audit`。
- Base commit：`657a39d finalize v4.8 system evaluation`。
- V4.8 已进入稳定 `main`。
- 本次审计没有修改 production code、README、AGENTS、evaluation dataset 或 frozen report。

### 2.2 Frozen technical facts

| Area | Frozen fact |
| --- | --- |
| Application | 单本汽车用户手册的本地 text-only RAG 问答应用 |
| Answer model | `qwen3.5:9b` |
| Generation | `think=false`、`temperature=0.0`、`seed=42`、`stream=false` |
| Retrieval | Dense + BM25 + RRF hybrid |
| Default rerank | `false` |
| Retrieval top_k | 5 |
| Context | metadata-aware selection、neighbor expansion=false、max_contexts=5、max_context_chars=6000 |
| Retrieval benchmark | 69 records / 68 active / 1 excluded |
| Frozen no-rerank metrics | Hit@1 0.6618、Hit@3 0.9265、Hit@5 0.9706、MRR 0.7922 |
| Answer evaluation | 12-case dev diagnostic set |
| Final proposed human result | Full Pass 10/12；不是 production accuracy |
| Runtime stability | 当前固定环境下 4 cases x 3 runs exact-output VERIFIED |
| User entry points | CLI、FastAPI、Streamlit |

### 2.3 Thirty-second to five-minute review

| Reviewer question | Current result | Reason |
| --- | --- | --- |
| 30 秒知道项目是什么 | PARTIAL | 首段说明是 text-only RAG，但以“练习 Python/评测/工程复盘”为中心，不是用户问题与应用价值。 |
| 1 分钟知道技术栈 | YES | Python、FastAPI、Ollama、Chroma、BM25、RRF 都能找到，但缺一个紧凑技术栈区。 |
| 2 分钟理解 architecture | PARTIAL | README 有两份文本流程，但不包含 API/UI 用户入口，也没有一张适合快速扫描的架构图。 |
| 3 分钟看到可信 evaluation | YES | 指标、样本规模和边界充分；但信息过多，招聘者难以识别最重要的三四个结论。 |
| 知道如何运行 | NO | README 从 ingest 命令开始，缺 clone、Python、venv、安装、Ollama、模型拉取、`.env` 和手册准备。 |
| 理解工程 trade-off | YES | no-rerank 默认、模型选择、text-only 限制和评测边界有证据支持。 |
| 判断不是 API wrapper | YES | parser、hybrid retrieval、hygiene、evaluation 和 reproducibility 都有真实代码。 |
| 有可运行 Demo 的信心 | NO | UI/API 存在，但没有截图、示例请求、预期输出或 fresh-clone 数据边界说明。 |
| AI 自动生成观感可控 | NO | README、报告数量、版本术语和全大写状态字段过重。 |

## 3. README Audit

### 3.1 Section-by-section decision

| Current section | Decision | Portfolio reason |
| --- | --- | --- |
| Title + opening | REWRITE | “项目说明”和“阶段性内部说明”直接表明它不是对外 README；应改为应用名称、一句话用户价值、核心栈和 Demo 信号。 |
| 1. 项目定位 | REWRITE | 当前以 parser/retrieval/evaluation 为主，缺汽车用户“从长手册中获得可溯源答案”的问题定义和 API/UI 应用形态。 |
| 2. 当前版本状态 | MOVE + MERGE | 30 多个状态点和版本名适合 milestone 文档；README 只保留当前稳定配置与 5-8 个能力。 |
| 3. 为什么不只是简单切块 | KEEP + REWRITE | 领域难点能证明应用价值，应压缩为 4-5 点并连接到对应工程决策。 |
| 4. 系统整体流程 | KEEP + REWRITE | 真实且重要；改成一张 Mermaid 架构图，并加入 FastAPI/Streamlit/CLI 与 answer/citation 出口。 |
| 5. Parser 设计 | MOVE | exact whitelist、subsection heuristics 等细节移至设计文档，README 只保留 manual-aware parsing 的 WHY。 |
| 6. Chunking 与 Metadata | MERGE | 与 parser/core features 合并；保留 hierarchy、safety metadata、citation 价值，不展示内部字段全集。 |
| 7. Retrieval 设计 | MERGE | 合并到 Architecture/Core Features/Trade-offs；保留 dense+BM25+RRF 和 rerank optional 决策。 |
| 8. Evaluation 设计 | MERGE + MOVE | 主 README 只保留评测方法和 claim boundary；multi-gold、validator 细节链接到 `docs/evaluation.md`。 |
| 9. V3.5 评测结果 | MERGE | 变成一张小型 Evaluation Snapshot；不要单独展开历史配置和 adjudication。 |
| 10. 已确认技术结论 | MERGE | 有价值的结论合并进 Design Decisions 和 Trade-offs，避免与前文重复。 |
| 11. 当前不应继续做的事 | REMOVE | 属于 AGENTS/工程治理，不是招聘者需要的产品说明。 |
| 12. 下一阶段方向 | REWRITE | 只保留克制的 Future Work；删除版本收尾和内部优先级流水账。 |
| 13. 常用命令 | REWRITE | 当前是高级维护命令集合；应先提供可复制 Quick Start，再把 inspection/evaluation 放到 Advanced Usage。 |
| 14. 项目结构 | KEEP + REWRITE | 当前树已过时，缺 answer evaluation、provenance、human adjudication 等模块；对外版只展示关键目录。 |
| 15. Known Limitations | KEEP + REWRITE | 内容真实，是可信度信号；压缩并放在评测之后。 |
| 16. 面向简历的可提炼亮点 | REMOVE | README 不应告诉招聘者“可以提炼什么”；应让架构、结果和 trade-off 自己证明能力。 |
| 17. Git 提交注意事项 | MOVE | 放入 AGENTS 或未来 CONTRIBUTING；README 只保留测试命令和数据版权边界。 |

### 3.2 Missing sections to add

- Product-first one-liner and application workflow。
- Core Features，限制为 5-8 项。
- Demo screenshot and one real example Q&A with citations。
- Fresh-clone Quick Start。
- CLI、FastAPI 和 Streamlit usage，含明确 URL/API payload。
- Concise Evaluation Snapshot。
- Architecture diagram。
- Key Decisions / Trade-offs。
- Curated links to design and frozen evaluation evidence。

### 3.3 Main README diagnosis

- 项目定位：技术事实准确，但用户问题和应用价值不够突出。
- 开头：过长且带“内部说明”免责声明，构成 public portfolio blocker。
- 开发历史：V3/V4 版本演进比产品主线更显眼。
- Evaluation：可信但过密，读者需要先理解内部术语才能读指标。
- Architecture：存在真实流程，但缺可扫描图示和应用入口。
- Quick Start：缺失。
- Demo：缺失展示资产。
- Future Work：范围已较克制，但仍应从版本路线改为用户/工程能力边界。
- 重复：版本状态、技术结论、评测结果和后续路线多次表达相同事实。
- Claim boundary：整体严谨，应保留这种克制风格。

**README_PORTFOLIO_READY = NO**

## 4. Architecture Audit

### 4.1 Code-supported application architecture

```text
Automotive Manual PDF
        |
PDFLoader + text cleaning
        |
ManualStructureParser
        |
Structured ManualBlock / Chunk + hierarchy metadata
        |
  +-----+-----+
  |           |
Chroma      BM25
dense       sparse
  |           |
  +-- RRF Hybrid Fusion --+
                          |
               TOC/noise filtering
               + exact content dedup
                          |
               metadata-aware context selection
               + final Evidence budget
                          |
               grounded Answer Prompt
                          |
               Ollama qwen3.5:9b
                          |
               Answer + structured citations
                          |
             CLI / FastAPI / Streamlit
```

代码支持该描述：ingest 由 `PDFLoader`、cleaner、`ManualStructureParser`、`ManualStructureSplitter` 和双索引组成；`HybridRetriever` 实现 dense/BM25/RRF；QAChain 串联 filter、dedup、context selection、Evidence budget、Ollama 和 citations；API、CLI、Streamlit 提供三种入口。

Optional cross-encoder rerank 应画成 RRF 后的可选分支，不能表现为稳定默认链路。

### 4.2 README 中最值得展示的组件

1. Manual-aware parsing and hierarchical metadata。
2. Dense + BM25 + RRF hybrid retrieval。
3. Index/retrieval hygiene and content dedup。
4. Metadata-aware final Evidence assembly with explicit budget。
5. Grounded local generation with structured citations。
6. CLI/FastAPI/Streamlit application surfaces。
7. 独立 evaluation/traceability sidecar，用于证明质量而不是替代应用主线。

**ARCHITECTURE_STORY_CLEAR = YES**。当前实现足以支撑清晰叙事，但 README 呈现尚未充分利用它。

## 5. Core Feature Audit

建议最终 README 只展示以下 7 项：

| Core feature | WHAT | WHY | Repository evidence |
| --- | --- | --- | --- |
| End-to-end local AI application | CLI、FastAPI、Streamlit 共用同一 QAChain 和本地 Ollama | 证明不仅有离线检索脚本，还有可交互应用与后端接口 | `app/main.py`、`app/api/`、`frontend/streamlit_app.py`、`scripts/query_manual.py` |
| Manual-aware ingestion | 恢复 chapter/section/subsection/heading_path，并保留 safety/content metadata | 汽车手册 PDF 丢失视觉层级，固定字符切块无法可靠保留主题和安全语义 | `manual_structure_parser.py`、`manual_structure_splitter.py`、parser tests |
| Hybrid retrieval | Chroma dense 与 BM25 sparse 双路召回，通过 RRF 融合 | 同时覆盖语义问题与术语/精确表达，避免依赖单一分数尺度 | `chroma_retriever.py`、`bm25_retriever.py`、`hybrid_retriever.py` |
| Evidence hygiene and context assembly | TOC/noise filter、exact content dedup、metadata-aware selection、5/6000 Evidence budget | 防止目录、重复块和上下文膨胀污染回答 | `chunk_filters.py`、`context_selector.py`、`qa_chain.py` |
| Grounded answers with citations | 模型只接收有边界的 Evidence；答案返回 page/chapter/section/quote 等引用 | 提升可核验性，适合安全相关汽车手册场景 | `answer_prompt.py`、`qa_chain.py`、`models.py` |
| Evaluation and traceability | retrieval/answer datasets、benchmark validation、exact Prompt Evidence、raw/final answer trace、human rubric | 让系统改动可比较，避免靠少量示例或主观观感调参 | `app/evaluation/`、`scripts/evaluate_*`、frozen reports |
| Reproducible local model selection | 显式固定 generation 参数，以不变 Prompt Evidence 比较三种本地模型 | 展示质量、成本和可部署性的工程权衡 | V4.7 selection 与 stability artifacts、`.env.example` |

## 6. Engineering Depth

### TOP_ENGINEERING_SIGNALS

1. **领域结构恢复**：parser/splitter 不只按字符切块，而是恢复层级、跨页 block、content/risk 类型，并有针对性单元测试。
2. **可解释混合检索**：dense、BM25、RRF 三种模式可独立运行，保留 source/rank/score metadata。
3. **索引卫生与诊断**：TOC/noise filtering、content dedup、`inspect_chunks`、stage-level debug 解决真实 PDF corpus 污染问题。
4. **严格 Evidence 边界**：最终送入 Prompt 的 Evidence 与 citations 使用同一组 contexts，并记录 exact Evidence snapshot。
5. **Benchmark consistency validation**：chunk strategy 变化后重校准 gold，支持 excluded/multi-gold/fail-fast，避免 stale benchmark 被误判为 regression。
6. **双层评测**：retrieval metrics 与 answer rubric 分离，自动 proxy 不覆盖人工 groundedness 判断。
7. **受控实验纪律**：V4.6 的失败 Prompt intervention 被正式 REJECT 且没有进入稳定系统，证明项目能保留负结果并控制变量。
8. **可复现本地部署决策**：记录 Ollama version、model digest、think/temperature/seed，并在固定环境验证 repeated-run exact output。

补充工程信号：配置集中在 `Settings`/`.env.example`；结构化日志贯穿 ingest/retrieval/QA；110 个显式 test functions、当前全量执行为 159 tests；CLI 提供 ingestion、query、inspection、validation 和 evaluation。

## 7. Evaluation Presentation

### 7.1 Current presentation

当前 README 对评测方法和 claim boundary 的严谨度高，但展示方式更像研究日志：读者要穿过 dataset recalibration、multi-gold、多个版本和 rerank 细节后，才能理解最终应用质量。对 AI Application Engineer Portfolio，应先展示“系统解决了什么、怎么验证”，再链接完整方法。

### 7.2 SAFE_PORTFOLIO_METRICS

| Metric | Dataset size | Meaning | Required claim boundary |
| --- | ---: | --- | --- |
| Hybrid no-rerank Hit@1 = 0.6618 | 68 active retrieval dev queries | top-1 chunk 命中任一 independently sufficient gold evidence 的比例 | 不是 answer accuracy，也不是跨手册效果 |
| Hybrid no-rerank Hit@3 = 0.9265 | 68 active retrieval dev queries | gold evidence 在前三个候选中的命中比例 | 只反映当前 V3.5 chunk/index 的 retrieval ranking |
| Hybrid no-rerank Hit@5 = 0.9706 | 68 active retrieval dev queries | 66/68 cases 的 gold evidence 进入 top-5 | 可称 candidate evidence recall proxy，不可称 97% accuracy |
| Hybrid no-rerank MRR = 0.7922 | 68 active retrieval dev queries | 首个正确 gold chunk 排名的倒数均值 | 仅适用于冻结 dev benchmark |
| Optional rerank Hit@1 = 0.8676 / Hit@5 = 1.0000 | 68 active retrieval dev queries | cross-encoder 在当前 benchmark 上改善 top-1 排序并使 gold 进入全部 top-5 | rerank 默认关闭；历史 elapsed 约翻倍，不是正式 latency benchmark |
| PROPOSED Human Full Pass = 10/12 | 12 answer dev diagnostic cases | 五维 frozen rubric 全部通过且无 unsupported/safety flag 的 proposed review | 必须写 PROPOSED、12-case dev diagnostic；不是 final human production accuracy |
| Prompt Evidence invariant = 12/12 | 3-model controlled comparison | 三模型看到的 Evidence identity/order/text 相同 | 支持模型选择因果解释，不代表模型总体能力 |
| Exact-output stability = 4 cases x 3 runs | 当前固定本机环境 | Prompt Evidence、raw/final answer 在重复运行中一致 | 不代表跨硬件/版本/backend 确定性 |

### 7.3 Recommended README evaluation block

主 README 只保留：默认 no-rerank 的四个 retrieval 指标、一句 optional rerank trade-off、一句 12-case answer diagnostic 结果及严格边界、一句 model-selection/reproducibility 证据。其余内容链接到 `docs/evaluation.md` 和 V3.5/V4.8 summary。

**EVALUATION_PRESENTATION_READY = NO**。数据可信，但尚未压缩为招聘者可快速理解的 supporting evidence。

## 8. Quick Start Audit

| Step | Status | Finding |
| --- | --- | --- |
| 1. clone | MISSING | README 没有 clone/cd 示例。 |
| 2. create environment | MISSING | 直接假设 `.venv/bin/python` 已存在；未说明支持的 Python 版本。 |
| 3. install dependencies | MISSING | 没有 `pip install -r requirements.txt`。 |
| 4. prepare Ollama | MISSING | 没有安装/启动/健康检查说明。 |
| 5. pull `qwen3.5:9b` | MISSING | README 展示模型名，但没有 pull 或验证命令。 |
| 6. configure `.env` | MISSING | 没有从 `.env.example` 创建本地配置的步骤。 |
| 7. prepare and ingest manual | PARTIAL | ingest 命令与 CLI 一致，但没有说明将合法获得的 PDF 放到何处、默认文件名、首次 embedding 下载和 BM25/Chroma 输出。 |
| 8. run first query | DOCUMENTED | `query_manual.py --question ... --retrieval-mode hybrid` 与 CLI 一致。 |
| 9. run API/UI | PARTIAL | 启动命令正确，但没有说明要同时运行后端与 Streamlit、访问 URL、`/docs` 或 `/query` 请求示例。 |
| 10. run evaluation | PARTIAL | retrieval/validation 命令充分；没有 answer evaluation 快速入口，也没有说明 fresh clone 缺原始手册/index 时无法复现 frozen benchmark。 |

关键可复现边界：`data/raw/train_a.pdf`、Chroma 和 BM25 index 按设计不提交。新 reviewer 无法仅从 clone 复跑冻结 benchmark。V5.0-B 必须清楚说明“自带合法手册运行应用”与“读取已提交 frozen reports”是两个不同路径；不能为方便而提交版权受限 PDF 或本地 index。

**QUICKSTART_READY = NO**

## 9. Demo Audit

### 9.1 Existing surfaces

- **CLI**：最可靠的开发者入口，可直接问答，也可查看 retrieval debug。
- **FastAPI**：实际提供 `/health`、`/ingest`、`/query`，并天然具备 OpenAPI `/docs`，但 README 未展示请求/响应。
- **Streamlit**：具备问题输入、top_k、retrieval mode、答案和 citations 展示；需要独立 FastAPI 后端。当前 citations 是长串调试字段，可用但不适合作为第一屏 Portfolio 演示。

### 9.2 Recommended portfolio demo

最佳展示入口是 **Streamlit + FastAPI 组合 Demo**：Streamlit 展示用户工作流和引用，FastAPI `/docs` 证明后端接口，CLI 作为开发者/诊断入口。不要新增 Agent 或大型前端。

### 9.3 Minimum V5.0-B improvements

1. 提供一张真实 Streamlit 问答截图，包含问题、简洁答案、页码/章节/quote 引用。
2. README 给出两个终端启动顺序、访问 URL 和一个 `/query` curl 示例。
3. Streamlit 默认视图只显示用户关心的 source/page/section/quote；rank/score/debug metadata 放入可展开区域。
4. 明确“尚未 ingest / 后端不可用 / Ollama 不可用”的运行前提和错误提示。
5. 加入一个基于已冻结 artifact 的静态 Example Q&A，避免要求招聘者先下载模型才能理解效果。

当前仓库没有 PNG/JPG/GIF/SVG/WebP Demo 资产。

**DEMO_READY = NO**

## 10. Repository Hygiene

### 10.1 BLOCKER

1. **IDE 配置已提交**：`.idea/` 下 6 个文件被 Git 跟踪，与 AGENTS 的提交规则冲突。公开发布前应从 index 移除并加入 `.gitignore`，但不能删除用户本地 IDE 配置。
2. **Fresh-clone 运行边界未说明**：原始 PDF、Chroma 和 BM25 index 正确地没有提交，但 README 没有解释数据版权、BYO-manual 流程和 frozen reports 与可复跑 benchmark 的区别。当前 Quick Start 对外不可执行。

### 10.2 SHOULD_FIX

1. 已跟踪 `reports/evaluation/` 共有 48 个文件、约 3.0 MB。没有 current/frozen/historical 索引，招聘者容易把开发过程当作项目主体。
2. 工作区另有多份历史 untracked docs/reports。发布前需要逐项分类，不应使用批量 add 或 clean。
3. `reports/evaluation/v4_5_1_generation_reproducibility.md` 含两处 `/Users/fruiterer/...` 绝对路径，属于 machine-specific 内容。
4. `.gitignore` 未显式包含 `.idea/` 和 `.pytest_cache/`；当前 `.DS_Store`、`.env`、logs、raw/index 已正确忽略。
5. `requirements.txt` 全部未锁版本，README 也没有 Python 版本；fresh-clone 依赖可复现性不足。
6. README 一边建议生成报告默认不提交，一边仓库保留大量报告，缺少“哪些是长期冻结资产”的治理说明。
7. README 项目结构已落后于真实代码，缺 answer evaluator、provenance、human adjudication、generation reproducibility 等关键能力。
8. 当前没有 LICENSE；如果仓库公开并希望允许复用，应明确授权边界。

### 10.3 OPTIONAL

- 创建 release tag 和简洁 changelog。
- 增加只跑 compile/tests 的轻量 CI。
- 提供依赖 constraints/lock 文件。
- 为长期报告建立 `reports/evaluation/README.md` 索引，历史报告可保留但降低主导航权重。

### 10.4 Positive findings

- 未发现已跟踪 `.env` 或明显 secret。
- 原始 PDF、46 MB Chroma、8.3 MB processed index 和 logs 均未被 Git 跟踪。
- 没有超过 500 KB 的单个 tracked file。
- `.DS_Store` 已忽略。
- 本次审计没有触碰既有 `app/core/exceptions.py` 修改或历史 untracked files。

**REPOSITORY_HYGIENE_READY = NO**

## 11. AI-Generated Smell Audit

**AI_GENERATED_SMELL_RISK = HIGH**

风险来自展示方式，不是否定技术真实性：

1. README 572 行，以阶段状态、内部术语和版本演进开场。
2. 48 份 tracked evaluation reports 与大量 V3/V4 文件名占据仓库可见面，但缺一个面向读者的导航层。
3. 文档频繁使用 frozen、gate、artifact、adjudication、全大写 flag 等流程语言，超过理解应用所需的信息量。
4. README 有“面向简历可提炼亮点”和“当前不应做什么”等元叙事，像开发代理的工作说明。
5. 没有截图、GIF、Example Q&A 或可复制 Quick Start，导致“过程文档很多、产品证据很少”的反差。

最重要的 5 个改善建议：

1. 把 README 重写为 product-first 结构，目标控制在约 180-260 行；详细版本历史全部链接出去。
2. 首屏加入一句话价值、核心架构图、Demo 截图和一个真实 Example Q&A。
3. 将评测压缩成一张可信小表，显式写样本规模和 claim boundary；建立报告索引区分 current、frozen、historical。
4. 从主 README 移除 agent/process 语言和大多数 ALL_CAPS flags，只保留用户能力、工程决策、结果与限制。
5. 完成 release hygiene：移除 tracked IDE metadata、修复绝对路径、整理未跟踪历史资产、给出明确 release checkpoint。

## 12. Resume Narrative

### PROJECT_PROBLEM

汽车用户手册长、结构复杂且包含安全敏感内容，用户难以快速定位与具体操作、告警或限制条件直接相关的原文。目标是在本地环境提供可追溯到页码和章节的问答，而不是依赖模型常识。

### CORE_TECHNICAL_CHALLENGE

PDF 抽取丢失标题层级和视觉结构；目录/页眉/表格残片污染索引；相近章节和汽车术语同时考验语义与关键词召回；安全条件、适用状态和跨 Evidence 列表必须在有限上下文中保留。

### KEY_ENGINEERING_DECISIONS

- 使用 manual-aware parser/splitter 恢复 hierarchy，而不是只做 fixed-size chunks。
- 用 Chroma dense + BM25 sparse + RRF 兼顾语义和术语召回。
- 在检索后加入可解释 hygiene、dedup 和 metadata-aware Evidence assembly。
- 使用本地 Ollama 模型、结构化 citations 和 exact Prompt Evidence trace 保持隐私与可审计性。
- 将 retrieval、answer、人工 rubric 和 reproducibility 分层评测，拒绝 case-specific 调参。

### MEASURABLE_RESULTS

- 在 68 条 active retrieval dev queries 上，默认 hybrid no-rerank 达到 Hit@1 0.6618、Hit@3 0.9265、Hit@5 0.9706、MRR 0.7922。
- optional cross-encoder rerank 将同一 dev benchmark 的 Hit@1 提升到 0.8676、Hit@5 提升到 1.0000，但历史单次 elapsed 约翻倍，因此没有默认启用。
- 三模型比较保持 12/12 Prompt Evidence 完全一致，最终选择更小、更快且条件处理更好的 `qwen3.5:9b`。
- 最终 12-case answer dev diagnostic run 的 PROPOSED Human Full Pass 为 10/12；该结果不是 production accuracy。

### FAILURE_DRIVEN_IMPROVEMENT

项目发现并修复过 stale benchmark、TOC/noise、content duplicate、Evidence/citation 不一致等工程问题；V4.6 的通用 Prompt intervention 在受控实验中未达到目标，被明确 REJECT；随后通过保持 Evidence 不变的模型比较解决主要 condition-handling failure。该过程比“只展示最好结果”更能证明工程判断。

### FINAL_TRADEOFF

最终版本选择 hybrid no-rerank 作为默认，保留 rerank 作为高精度可选项；选择 6.6 GB `qwen3.5:9b` 而不是更大的 `gemma3:12b`；保持 text-only、单手册、本地部署边界，不为简历效果加入缺少证据的 Agent、GraphRAG、query rewrite 或云服务。

当前 repository 已具备这条叙事的全部证据，但 README 尚未按该顺序表达。

**RESUME_NARRATIVE_READY = NO**：叙事素材已齐全，公开呈现尚未完成。

## 13. Missing Portfolio Assets

| Asset | Priority | Current state / rationale |
| --- | --- | --- |
| Product-first README | MUST_HAVE | 当前明确自称阶段性内部说明。 |
| Fresh-clone Quick Start | MUST_HAVE | clone/env/install/Ollama/model/config/manual steps 缺失。 |
| Architecture diagram | MUST_HAVE | 实现支持清晰架构，但当前只有内部文本流程。 |
| Demo screenshot | MUST_HAVE | AI 应用岗位需要快速证明可交互体验；当前无任何视觉资产。 |
| Real Example Q&A + citation | MUST_HAVE | 招聘者无法在不安装模型时看到应用输出。 |
| Concise evaluation summary | MUST_HAVE | 指标已存在，但需按 dataset/meaning/boundary 压缩。 |
| Data/manual reproducibility statement | MUST_HAVE | 必须解释版权手册不提交以及 fresh clone 可复现到什么程度。 |
| API curl + `/docs` instructions | HIGH_VALUE | FastAPI 已实现，补文档成本低、能证明 backend 能力。 |
| Report/document index | HIGH_VALUE | 48 份 report 需要 current/frozen/historical 导航。 |
| Dependency/Python compatibility | HIGH_VALUE | 当前 requirements 无版本、Python 未说明。 |
| LICENSE | HIGH_VALUE | 公开仓库应明确代码复用边界。 |
| Release tag/checkpoint | HIGH_VALUE | 帮助招聘者定位稳定版本。 |
| Project structure | HIGH_VALUE | 已存在但需更新和缩短。 |
| Design decisions/trade-offs | HIGH_VALUE | 内容分散，适合一张表。 |
| Demo GIF | OPTIONAL | 截图足够后再决定，不是 blocker。 |
| Lightweight test CI | OPTIONAL | 能增加可信度，但本地模型/索引不适合直接放入常规 CI。 |
| Dependency lock/constraints | OPTIONAL | 高于完全不锁版本，但可以在 README 重构后处理。 |
| Docker/cloud deployment | NOT_NEEDED | 本阶段本地 Ollama 路径清楚，不值得为作品集扩大运维范围。 |
| Agent workflow | NOT_NEEDED | 应作为独立项目；本项目保持纯 RAG application 定位。 |
| 新检索/模型 benchmark | NOT_NEEDED | 技术主线已冻结，不是 Portfolio gap。 |

## 14. Target README Structure

建议最终 README 目录：

1. **Auto Manual RAG**：一句话用户问题与价值，3-5 个技术标签。
2. **Demo**：一张 Streamlit 截图、一个问题/答案/引用示例、入口说明。
3. **Why This Application**：汽车手册结构、安全和可追溯性挑战。
4. **Core Features**：7 项以内，使用 WHAT/WHY 而不是版本号。
5. **Architecture**：一张 Mermaid 图，区分默认链路与 optional rerank/evaluation sidecar。
6. **Quick Start**：环境、Ollama、模型、`.env`、手册、ingest、first query。
7. **Usage**：Streamlit、FastAPI/curl、CLI/debug。
8. **Evaluation Snapshot**：默认 retrieval、optional rerank、answer diagnostic、reproducibility；每项带样本规模和边界。
9. **Key Engineering Decisions**：hybrid、no-rerank 默认、模型选择、Evidence budget、本地部署。
10. **Known Limitations**：text-only、single manual、data availability、非 production benchmark。
11. **Project Structure**：简化后的关键目录。
12. **Documentation**：只链接 architecture/evaluation/frozen summary/experiment history 的索引。
13. **Future Work**：多手册、多模态、正式 latency 等少量方向，不承诺 Agent。
14. **License**。

版本时间线、parser 规则细节、benchmark recalibration、全部实验表格和 Git/agent 约束不放在主 README，分别留在 docs、reports 和 AGENTS。

## 15. V5.0-B Prioritized Plan

最多执行以下 10 项，不加入新 RAG 算法：

### P0

| Task | Why | Files | Acceptance Criteria |
| --- | --- | --- | --- |
| 1. Product-first README rewrite | 解决首屏内部文档化、应用价值弱和 572 行信息过载 | `README.md` | 3-5 分钟可读；首屏包含问题、价值、技术栈、Demo；正文约 180-260 行；无版本流水账和简历元叙事。 |
| 2. Runnable Quick Start and data boundary | 当前 fresh clone 无法按 README 建环境或理解手册/index 缺失 | `README.md`、必要时 `.env.example` 注释 | 从 clone 到 first query 步骤完整；命令通过 `--help` 核对；明确 BYO licensed manual、默认路径和 frozen report 复现边界。 |
| 3. Architecture + application workflow | 将工程组件组织成 AI Application pipeline，而不是算法列表 | `README.md` | Mermaid 与真实代码一致；包含 CLI/API/UI、默认 no-rerank 和 evaluation sidecar；不虚构 Agent/GraphRAG。 |
| 4. Demo evidence pack | 当前没有任何视觉或示例输出，无法快速证明应用可用 | `docs/assets/` 或等价目录、`README.md` | 一张可读截图；一个真实问题/答案/引用示例；无手册大段版权文本、隐私路径或虚构回答。 |
| 5. Public repository hygiene | tracked IDE、绝对本机路径和报告噪声会降低可信度 | `.gitignore`、Git index、相关 report、可选 report index | `.idea` 不再 tracked；无绝对本机路径；current/frozen/historical reports 有清楚导航；不误删用户本地/历史资产。 |

### P1

| Task | Why | Files | Acceptance Criteria |
| --- | --- | --- | --- |
| 6. Minimal UI/API presentation polish | Streamlit 目前展示长串 debug 字段，FastAPI 使用方式不可见 | `frontend/streamlit_app.py`、`README.md`，必要 tests | 默认 citation 以 source/page/section/quote 为主，诊断字段可展开；README 有 `/health`、`/query` 和 `/docs` 示例；不重构前端。 |
| 7. Concise evaluation and trade-off presentation | 把评测从主体降为可信 supporting evidence | `README.md`、可选 `reports/evaluation/README.md` | 一张小表含样本规模/含义/边界；链接 V3.5/V4.8 summary；明确 rerank 质量/成本取舍和 10/12 PROPOSED 属性。 |
| 8. Runtime/dependency reproducibility note | requirements 未锁版本且 Python 版本不明 | `README.md`、`requirements.txt` 或轻量 constraints 文件 | 记录已验证 Python/Ollama 版本；安装命令明确；如锁版本，不引入新的包管理框架。 |
| 9. Release identity and licensing | 公共作品集需要稳定入口和代码授权边界 | `LICENSE`、Git tag/release notes、README | 明确 license；创建可解释的 V5.0 release checkpoint；不包含模型权重、PDF 或 index。 |

### P2

| Task | Why | Files | Acceptance Criteria |
| --- | --- | --- | --- |
| 10. Optional presentation automation | 在核心资产完成后补充持续可信度 | 可选 `.github/workflows/` 或 Demo GIF | 只做无需 Ollama/index 的 compile/unit tests，或制作短 GIF；不得引入 Docker/cloud/Agent scope。 |

## 16. Portfolio Gate

- `TECHNICAL_CORE_READY = YES`
- `README_PORTFOLIO_READY = NO`
- `QUICKSTART_READY = NO`
- `DEMO_READY = NO`
- `REPOSITORY_HYGIENE_READY = NO`
- `EVALUATION_PRESENTATION_READY = NO`
- `RESUME_NARRATIVE_READY = NO`
- `AI_GENERATED_SMELL_RISK = HIGH`
- `READY_FOR_V5_0_B = YES`

这里的 `READY_FOR_V5_0_B = YES` 表示审计已形成明确、有限的 hardening backlog，不表示 Portfolio 已经 ready。V5.0-B 应从 P0 开始，停止新增 RAG/Agent 功能。
