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

## 8. Git 与提交规范

建议使用清晰的 commit message，例如：

- init project skeleton
- add pdf loader
- implement basic chunk splitter
- add chroma retriever
- implement ollama llm client
- add streamlit demo
- add retrieval evaluation script

不要把以下内容提交到 Git：

- .env
- 原始 PDF 手册
- 本地 Chroma 数据库
- processed 中间文件
- __pycache__
- 大模型权重文件

## 9. 当前版本路线

项目迭代路线：

- V0：项目初始化
- V1：最小 RAG 闭环
- V2：汽车手册结构化解析
- V3：检索优化，包括 hybrid search、rerank、metadata filter
- V4：安全回答策略与引用溯源
- V5：问答评估体系
- V6：前端展示与工程化打磨

## 10. 对 Codex 的特别要求

每次 Codex 修改项目时，输出必须包含：

1. 本次任务目标
2. 修改的文件列表
3. 核心实现说明
4. 如何运行
5. 如何测试
6. 是否有未完成事项
7. 下一步建议

并且不要在没有明确要求的情况下跨版本实现后续功能。
