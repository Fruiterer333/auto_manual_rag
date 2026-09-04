# Auto Manual RAG v5.0 Resume-Ready Release Notes

## Highlights

- 提供汽车用户手册 PDF 的本地、可追溯问答应用。
- 支持 CLI、FastAPI 和 Streamlit 三种入口，回答返回页码、章节和证据摘录。
- 使用 `qwen3.5:9b`、Ollama、显式 `temperature=0.0`、`seed=42`、`stream=false`、`think=false`。
- 完成产品优先 README、真实 Demo 截图、Quick Start、评测导航和简历/面试材料。

## Architecture

- PyMuPDF 加载与文本清洗。
- Manual-aware hierarchical parser/splitter，保留 chapter、section、subsection、heading path 和安全 metadata。
- Chroma Dense + BM25 Sparse 双路召回，使用 RRF 融合。
- TOC/noise filtering、exact content dedup、metadata-aware context selection。
- 最终 Evidence 限制为最多 5 条、6000 字符，由本地模型生成 grounded answer 和 structured citations。

## Evaluation Snapshot

- Retrieval dev benchmark：69 records、68 active、1 excluded、99 gold evidence，validator issues 为 0。
- Stable hybrid no-rerank：Hit@1 `0.6618`、Hit@3 `0.9265`、Hit@5 `0.9706`、MRR `0.7922`。
- 12-case single-manual answer dev diagnostic set：PROPOSED Human Full Pass `10/12`；不是 production accuracy。
- 三模型比较保持 12/12 Prompt Evidence identity/order/text invariant，最终选择 `qwen3.5:9b`。
- 当前固定环境完成 4 cases x 3 runs 的 Prompt Evidence/raw/final exact-output stability verification。

## Engineering Quality

- Retrieval benchmark 与当前 chunk strategy 对齐，支持 consistency validation、multi-gold 和 excluded cases。
- Answer artifacts 记录 Exact Prompt Evidence、raw answer、final answer、citations 和 generation/runtime metadata。
- 受控实验一次只改变一个主要变量；无效 Condition Preservation Prompt treatment 被 REJECT，未进入稳定系统。
- 配置集中在 Settings/`.env`，默认 rerank 和 neighbor expansion 均关闭。
- 原始手册、Chroma/BM25 index、模型权重、日志和本地配置不进入 Git。

## Known Limitations

- 当前只验证单本汽车用户手册，不代表跨品牌、跨车型能力。
- text-only pipeline 不处理图标、图片、OCR 或复杂表格布局。
- Answer diagnostic set 规模较小，逐 case 评分仍为 PROPOSED。
- complementary evidence 和 safety-critical evidence 仍可能未进入最终上下文。
- 本地 elapsed 不是正式线上 latency benchmark；重复运行稳定性不代表跨硬件/版本 determinism。
- fresh-clone 命令已核对，但尚未在全新机器完成模型下载、合法手册准备和完整索引重建。
- 开源许可证尚待仓库所有者决定；第三方汽车手册及其内容不随代码分发。

## Release Identity

- 推荐 tag：`v5.0.0`。
- 该 tag 表示 Resume-Ready application release，不改变 V3.5 frozen retrieval 或 V4.8 final evaluation artifacts。
- 技术开发在本 release 后进入 maintenance；后续只接受 bug fix、依赖维护、文档纠正和由新证据支持的独立实验。
