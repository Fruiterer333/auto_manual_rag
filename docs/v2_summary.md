# V2 Summary: Manual-aware RAG

## 目标

V2 的目标是将 V1 中基于 fixed-size / page-level 的 chunk 策略升级为面向汽车用户手册的 manual-aware chunk 策略。

## 已完成能力

- 识别汽车用户手册中的 chapter / section。
- 识别 warning / caution / note / procedure / normal 等 content_type。
- 标记 high / medium / low risk_level。
- 将 chapter、section、content_type、risk_level 写入 Chroma metadata。
- 在 debug retrieval 中展示结构化 metadata。
- 引入轻量 metadata-aware context selection。
- 修复回答中出现“资料4 / 片段1 / 上下文2”等内部编号的问题。
- 默认关闭效果不稳定的 neighbor context expansion。

## 已知限制

- 纯 dense retrieval 对相近小节区分能力有限，例如“安全带作用 / 使用安全带 / 安全带检查”。
- “充电”存在多义词干扰，可能召回无线充电、车内插座、动力电池充电等不同上下文。
- metadata-aware context selection 只能轻量纠偏，不能替代真正的 hybrid retrieval 或 rerank。
- 跨页上下文补全当前不稳定，默认关闭。

## 下一阶段

V3 将引入 hybrid retrieval，优先实现 BM25 sparse retrieval 与 dense retrieval 融合，改善关键词型问题、短查询、多义词和相近小节的召回排序问题。