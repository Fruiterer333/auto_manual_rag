# V3.1 Rerank Design Plan

## 1. Background

当前项目已经完成 V3.0 Hybrid Retrieval、V3.0.1 index hygiene 与 diagnostics、V3.0.2 retrieval evaluation framework，以及 V3.0.3 case-level cross-mode diagnostics。

> 状态更新：本文档最初基于 29 条 dev cases 设计 V3.1 rerank baseline，正文保留早期设计背景。V3.2 的历史结果见 [`docs/evaluation/rerank_evaluation_summary.md`](evaluation/rerank_evaluation_summary.md)；当前正式结论以 V3.5 frozen benchmark 总览 [`reports/evaluation/v3_5_retrieval_benchmark_summary.md`](../reports/evaluation/v3_5_retrieval_benchmark_summary.md) 为准。

V3.0.3 的历史 diagnostics 基于当时的 29 条 `dev` cases，报告显示：

- `dense`、`bm25`、`hybrid` 的 `evidence_hit@5` 均为 `1.0000`；
- BM25 当前 `evidence_hit@1` 和 MRR 略高；
- hybrid 尚未稳定超过 BM25；
- `hybrid + context selection` 的 `final_context_hit` 很高；
- 21 条 case 在三种 retrieval mode 下均 top-1 命中；
- 4 条 case 存在 `hybrid_worse_than_bm25`；
- 1 条 case 存在 `hybrid_worse_than_dense`；
- 1 条 case 属于 `top5_hit_but_no_top1`；
- 17 条 case 存在 top-1 section metadata 缺失。

这些结果说明当前主要瓶颈不是 top-5 召回失败，而是候选 chunk 之间的精排。context selection 已经能整理最终上下文，但它不是 reranker，不应继续叠加手写 bonus、penalty 或 query-specific 规则来承担强排序职责。

引入 rerank 的依据是当前 evaluation 报告，而不是为了继续堆功能。V3.1 的目标是验证一个可关闭、可回滚、可评测的本地 cross-encoder rerank baseline。

## 2. Problem Statement

当前链路存在以下通用排序问题：

1. 正确 evidence 已进入 top-5，但 top-1 可能不是最相关 chunk。
2. hybrid 的 RRF 融合可能破坏 BM25 或 dense 的单路强命中。
3. 同主题章节之间容易误排，例如功能说明、操作步骤、提醒和警告共享相近词汇。
4. 参数限制类、操作步骤类、安全提示类问题在部分 case 上存在候选排序偏差。
5. section metadata 缺失会降低人工诊断能力，但 rerank 不应依赖 section metadata 才能工作。

当前代表 case：

| case_id | 现象 | 设计解读 |
| --- | --- | --- |
| `seatbelt_fastening_001` | dense rank 1，BM25 rank 4，hybrid rank 2 | dense 已命中准确步骤，hybrid 被关键词相关但意图较弱的 chunk 拉偏 |
| `epb_enable_release_001` | dense rank 2，BM25 rank 3，hybrid rank 2 | 三路 top-1 都被相似章节误导，正确 evidence 已在 top-5 |
| `tire_repair_after_limits_001` | BM25 rank 1，dense rank 3，hybrid rank 2 | 参数限制类问题中 BM25 的字面匹配更准确 |
| `front_hood_open_001` | BM25 rank 1，dense rank 3，hybrid rank 3 | BM25 强命中被融合稀释，同时存在 section metadata 噪声 |

这些 case 用于解释通用问题，不是规则白名单，也不能成为 query-specific 优化条件。

## 3. Non-goals

V3.1 第一阶段不做：

- 不重写 parser 或 splitter；
- 不修改 eval dataset 来迎合 rerank；
- 不继续堆 BM25 规则、固定关键词或 query-specific penalty；
- 不用 context selection 替代 rerank；
- 不做 query rewrite；
- 不使用 LLM rerank；
- 不使用 LLM-as-judge 作为主评测方式；
- 不修改 answer generation prompt；
- 不为单个 case 编写特殊规则；
- 不引入复杂 agent workflow；
- 不在验证完成前改变默认 production behavior。

## 4. Proposed Pipeline

```text
User Query
  -> Dense / BM25 / Hybrid Retrieval
  -> Hygiene Filter / Dedup
  -> Cross-Encoder Rerank
  -> Context Selection
  -> Prompt Construction
  -> LLM Answer
```

rerank 的输入是 retrieval 层返回并经过 hygiene filter / dedup 清理后的 candidate chunks，不是原始 PDF，也不是全部索引文档。

rerank 的输出是重新排序后的 `RetrievedChunk` 列表。context selection 位于 rerank 之后，只负责上下文整理、长度控制、去重和 citation metadata 保留。

职责边界：

| 模块 | 负责 | 不负责 |
| --- | --- | --- |
| dense / BM25 / hybrid retrieval | 召回候选 chunk | 最终 query-chunk 精排 |
| hygiene filter / dedup | 清理 TOC、noise 和重复内容 | 判断复杂语义相关性 |
| cross-encoder rerank | 对 query-chunk pair 做 relevance 精排 | 扩大召回范围、修改 chunk、生成答案 |
| context selection | 整理 rerank 后上下文、控制长度、保留 citation metadata | 替代 rerank、叠加不可解释的业务规则 |
| LLM generation | 基于最终 context 回答 | 修复 retrieval 或 rerank 失败 |

## 5. Reranker Options

### Option A: Cross-Encoder Reranker

Cross-encoder 将 query 和 chunk 作为成对输入，联合编码后输出 relevance score。Sentence Transformers 官方文档说明，CrossEncoder 不生成可预计算的独立 embeddings，而是直接对输入 pair 打分；这会增加推理成本，但更适合 reranking 这类 pairwise relevance 判断。

优点：

- 对 query-chunk relevance 的判断强于仅依赖向量距离或关键词排名；
- 适合解决 top-5 已命中但 top-1 不准的问题；
- 预期可改善 `evidence_hit@1`、MRR 和 first-hit rank；
- 可以保持 retrieval mode 与 context selection 的既有职责不变。

缺点：

- 每次 query 都要对 candidate pairs 做模型推理；
- 本地推理延迟和内存占用会上升；
- 中文和中英混合手册效果必须通过项目 dev set 实测；
- CPU / MPS 的兼容性和速度不能只依据模型卡推断。

### Option B: Lightweight Heuristic Rerank

优点：

- 实现简单；
- 本地运行成本低；
- debug 较直接。

缺点：

- 容易围绕少量样例过拟合；
- 容易继续叠加 bonus、penalty 和 if-else；
- 会与 context selection 的轻量整理职责重叠；
- 当前已不适合作为 V3.1 主路线。

### Option C: LLM-based Rerank

优点：

- 具备较强语义理解能力；
- 对复杂自然语言意图可能有效。

缺点：

- 延迟高；
- 本地资源成本高；
- 输出稳定性和可复现性较差；
- 不适合作为当前 retrieval evaluation 主链路；
- 会扩大系统复杂度。

### Recommendation

推荐 Option A：Cross-Encoder Reranker。

V3.1 第一版只验证一个本地 cross-encoder baseline。不要同时引入多模型路由、LLM fallback 或启发式补丁。

## 6. Model Candidates

以下模型仅作为候选，必须在当前 MacBook M3 Pro 18GB 环境与 69 条 text-only dev set 上实测。模型卡中的 benchmark 不能替代本项目评测。

| 模型 | 官方信息摘要 | 适用判断 | 风险与待验证项 |
| --- | --- | --- | --- |
| [`BAAI/bge-reranker-base`](https://huggingface.co/BAAI/bge-reranker-base) | 官方模型卡标注 Chinese and English，基于 cross-encoder，定位为较易部署的基础 reranker | 适合作为第一版 baseline | 需要测量 CPU / MPS 延迟、内存和中文手册排序收益 |
| [`BAAI/bge-reranker-v2-m3`](https://huggingface.co/BAAI/bge-reranker-v2-m3) | 官方模型卡标注 multilingual，面向 query-passage relevance 打分 | 适合作为更强候选与 baseline 对照 | 模型更重，依赖路径、MPS 兼容性和延迟需实测 |
| [`BAAI/bge-reranker-large`](https://huggingface.co/BAAI/bge-reranker-large) | BGE 官方文档列为 Chinese and English 的更大 reranker | 可作为后续效果上限对照 | 本地资源成本更高，不应作为第一版默认 |
| [`jinaai/jina-reranker-v2-base-multilingual`](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual) | 官方模型卡标注 multilingual cross-encoder，并提供 Sentence Transformers 用法 | 可作为多语言备选 | 模型卡要求 `trust_remote_code=True`，许可证为 `CC-BY-NC-4.0`；商业使用边界和本地集成复杂度需单独评估 |
| [`mixedbread-ai/mxbai-rerank-base-v1`](https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v1) | 官方模型卡提供 Sentence Transformers `CrossEncoder` 用法 | 可作为英文或对照实验候选 | 官方标签偏 English，不应在中文手册场景中优先于 BGE |

选择标准：

1. 中文能力；
2. 本地推理成本；
3. 依赖复杂度；
4. 与当前 Python 项目的集成难度；
5. CPU / MPS / CUDA 设备支持；
6. MacBook M3 Pro 18GB 上的可接受性；
7. 单 query rerank 延迟和吞吐；
8. dev set 上的排序质量；
9. 许可证与部署边界。

Sentence Transformers 的 CrossEncoder API 接受 `device` 和 `max_length` 参数，并支持 `cpu`、`mps`、`cuda` 等 device 值。这里的“支持”是 API 层能力；具体模型在 Apple Silicon 上是否稳定、高效，仍需实测确认。

## 7. Recommended Initial Choice

第一阶段推荐：

```text
BAAI/bge-reranker-base
```

理由：

- 官方模型卡标注 Chinese and English；
- 适合 query-passage relevance rerank；
- 相比更大模型，适合作为本地工程 baseline；
- 初始目标是验证 pipeline、metadata 和 evaluation，而不是追求模型上限；
- baseline 无收益时，可以及时回滚，避免扩大依赖和复杂度。

第二阶段对照：

```text
BAAI/bge-reranker-v2-m3
```

理由：

- 官方模型卡标注 multilingual；
- 可作为更强候选，验证额外推理成本是否换来可量化收益。

推荐顺序是先用 `bge-reranker-base` 建立 baseline，再用相同 evaluation protocol 对比 `bge-reranker-v2-m3`。不要在没有 latency 与排序指标的情况下直接将更大模型设为默认。

## 8. Configuration Design

建议新增配置：

```dotenv
ENABLE_RERANK=false
RERANK_MODEL_NAME=BAAI/bge-reranker-base
RERANK_TOP_N=10
RERANK_OUTPUT_TOP_K=5
RERANK_DEVICE=auto
RERANK_BATCH_SIZE=8
RERANK_MAX_LENGTH=512
```

配置说明：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `ENABLE_RERANK` | `false` | 默认关闭，避免影响当前稳定链路 |
| `RERANK_MODEL_NAME` | `BAAI/bge-reranker-base` | baseline 模型，可替换 |
| `RERANK_TOP_N` | `10` | 只对 retrieval 候选 top-N rerank |
| `RERANK_OUTPUT_TOP_K` | `5` | rerank 后输出给 context selection 的候选数量 |
| `RERANK_DEVICE` | `auto` | 后续支持 `auto` / `cpu` / `mps` / `cuda` |
| `RERANK_BATCH_SIZE` | `8` | 控制吞吐和本地内存 |
| `RERANK_MAX_LENGTH` | `512` | 控制 query-chunk pair 截断长度 |

设计要求：

- 所有配置通过 `config.py` 和 `.env` 管理；
- 第一版默认 `ENABLE_RERANK=false`；
- `RERANK_TOP_N` 应至少覆盖当前 hybrid fusion 候选数量；
- `RERANK_OUTPUT_TOP_K` 不应大于 `RERANK_TOP_N`；
- `batch_size`、`max_length` 和 device 必须通过 latency 与内存测量调整；
- 不在业务代码中写死模型名。

## 9. Code Design

建议后续新增：

```text
app/rag/rerankers/
  __init__.py
  base.py
  cross_encoder_reranker.py
  noop_reranker.py
```

建议接口：

```python
from abc import ABC, abstractmethod

from app.data.schemas.models import RetrievedChunk


class BaseReranker(ABC):
    @abstractmethod
    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        ...
```

建议通过 `RetrievedChunk.metadata` 增加可选 debug 字段，避免破坏现有 API：

```text
rerank_score
original_rank
rerank_rank
rerank_model
rerank_enabled
rerank_elapsed_ms
```

如果后续需要更严格类型约束，可以增加内部结构：

```python
class RerankResult:
    chunk: RetrievedChunk
    rerank_score: float
    original_rank: int
    rerank_rank: int
    retrieval_source: str | None
```

第一版优先保持 `RetrievedChunk` 返回类型兼容，不急于扩大公共 schema。

## 10. Pipeline Integration

建议在 retrieval 后、context selection 前集成：

```python
retrieved = retriever.search(...)
filtered = filter_and_dedup(retrieved)
reranked = reranker.rerank(
    query=question,
    chunks=filtered[: settings.RERANK_TOP_N],
    top_k=settings.RERANK_OUTPUT_TOP_K,
)
selected = context_selector.select_contexts(
    question=question,
    retrieved=reranked,
    top_k=top_k,
)
```

约束：

- `dense` / `bm25` / `hybrid` 三种 retrieval mode 保持不变；
- rerank 是独立开关，不改变 retrieval mode 语义；
- `ENABLE_RERANK=false` 时使用 `NoopReranker`；
- Noop 路径必须保留原顺序和 metadata；
- debug retrieval 后续应展示 `rerank_score`、`original_rank`、`rerank_rank`；
- evaluation runner 后续应支持 rerank on/off 对比；
- context selection 继续作为轻量 organizer，不增加强排序规则。

## 11. Evaluation Plan

### Comparison Matrix

至少对比：

| retrieval mode | rerank | 目的 |
| --- | --- | --- |
| `hybrid` | off | 当前基线 |
| `hybrid` | on | 验证 rerank 是否修复融合退化 |
| `bm25` | off | 当前 MRR 较高的单路参考线 |
| `dense` | off | 可选参考线 |

如果成本可接受，再对比：

- `bm25 + rerank`；
- `dense + rerank`；
- `bge-reranker-base` 与 `bge-reranker-v2-m3`。

### Core Metrics

- `evidence_hit@1`
- `evidence_hit@3`
- `evidence_hit@5`
- `mrr`
- `average_first_hit_rank`
- `final_context_hit`
- `Hybrid Regressions count`
- `Top-5 Hit but Not Top-1 count`
- latency per query，包括平均值和高分位延迟

### Acceptance Direction

rerank 有效的必要条件：

1. `evidence_hit@1` 提升；
2. MRR 提升；
3. `evidence_hit@5` 不下降；
4. `final_context_hit` 不下降；
5. `Hybrid Regressions count` 减少；
6. `Top-5 Hit but Not Top-1 count` 减少；
7. 延迟增量可接受；
8. 不显著增加运行失败率或依赖维护成本。

代表 case 应用于人工解释结果：

- `seatbelt_fastening_001`
- `epb_enable_release_001`
- `tire_repair_after_limits_001`
- `front_hood_open_001`

这些 case 不能作为唯一验收标准。不要只看单个 case，不要为了提高 top-1 牺牲 top-5，不要使用 LLM-as-judge 作为主评测。

### Evaluation Integration

后续建议扩展 `evaluate_retrieval.py`：

- 增加 rerank on/off 参数；
- 在报告中记录 rerank model 和配置；
- 复用当前 all-modes 与 case-level diagnostics；
- 增加 rerank latency；
- 输出 rerank 前后 rank delta；
- 保留原始 retrieval rank，确保结果可解释。

## 12. Rollback and Risk Control

### Risks

- 本地推理变慢；
- 模型下载和依赖增加；
- CPU / MPS 支持表现不确定；
- 中文手册排序收益不一定稳定；
- 可能把原本 top-1 正确的 case 排错；
- 截断策略可能丢失长 chunk 后半段证据；
- 系统复杂度增加。

### Rollback Strategy

- 默认 `ENABLE_RERANK=false`；
- 提供 `NoopReranker`；
- 保留现有 dense / BM25 / hybrid retrieval；
- 保留 rerank 前原始 rank 和 score；
- evaluation 对比后再决定是否保留；
- V3.1 第一版不默认改变 production behavior；
- 如果收益不明确或延迟不可接受，关闭 rerank 并保留设计与评测记录。

## 13. Implementation Phases

### V3.1.0 Design and Interface

- 增加 reranker interface；
- 增加 `NoopReranker`；
- 增加配置结构；
- 不引入模型；
- pipeline 保持兼容。

### V3.1.1 Local Cross-Encoder Baseline

- 集成一个本地 cross-encoder；
- 支持配置开关；
- 支持 CLI evaluation；
- debug 输出 rerank metadata；
- 记录加载耗时和 query rerank 延迟。

### V3.1.2 Rerank Evaluation

- 对比 rerank on/off；
- 输出 rerank-specific metrics；
- 分析代表 case；
- 比较 `bge-reranker-base` 与必要的备选模型；
- 决定是否保留默认关闭。

### V3.1.3 Optimization

- batch inference；
- device auto；
- `max_length`；
- latency reporting；
- 仅在 baseline 有收益时比较更多 reranker 模型。

## 14. Acceptance Criteria

后续实现必须满足：

1. 不破坏现有 dense / BM25 / hybrid；
2. `ENABLE_RERANK=false` 时行为完全兼容；
3. Noop 路径不改变原顺序；
4. rerank metadata 可追踪；
5. debug retrieval 能显示 rerank 前后排名；
6. evaluation runner 能比较 rerank on/off；
7. `evidence_hit@5` 不下降；
8. `final_context_hit` 不下降；
9. 只有 `evidence_hit@1` 和 MRR 有量化提升，才认为 rerank 有效；
10. 不以单个 case 成败作为唯一依据；
11. 不默认启用未经评测验证的 rerank；
12. 可以通过单一开关回滚。

## 15. Open Questions

1. 第一版使用 `BAAI/bge-reranker-base`，还是直接使用 `BAAI/bge-reranker-v2-m3`？
2. 是否需要在第一版支持 MPS，还是先用 CPU 建立可复现 baseline？
3. `RERANK_TOP_N` 选择 `10` 还是 `20`？
4. 是否需要把 latency metric 纳入第一版 evaluation runner？
5. 是否需要将 rerank metadata 暴露到 API response？
6. 是否继续默认关闭 rerank，直到扩大 eval set 并完成 dev 对比？
7. 是否需要比较 `FlagEmbedding` 与 `sentence-transformers.CrossEncoder` 两种 backend？
8. 是否需要对长 chunk 评测 `RERANK_MAX_LENGTH` 截断影响？

## References

- [Sentence Transformers CrossEncoder documentation](https://sbert.net/docs/package_reference/cross_encoder/cross_encoder.html)
- [Sentence Transformers CrossEncoder usage](https://www.sbert.net/docs/cross_encoder/usage/usage.html)
- [BAAI/bge-reranker-base model card](https://huggingface.co/BAAI/bge-reranker-base)
- [BAAI/bge-reranker-v2-m3 model card](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- [BGE Reranker documentation](https://bge-model.com/bge/bge_reranker.html)
- [jinaai/jina-reranker-v2-base-multilingual model card](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual)
- [mixedbread-ai/mxbai-rerank-base-v1 model card](https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v1)
