"""Machine-readable consolidation of human answer-evaluation adjudications."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.evaluation.answer_evaluator import (
    AnswerCaseResult,
    AnswerEvaluationRun,
    HumanAnswerReview,
)


FailureLayer = Literal[
    "RETRIEVAL",
    "RANKING",
    "CONTEXT_SELECTION",
    "GENERATION",
    "EVALUATOR",
    "DATASET",
    "NONE",
    "UNCERTAIN",
]
AdjudicationStatus = Literal["completed", "final"]
HUMAN_SCORE_DIMENSIONS = (
    "groundedness",
    "correctness",
    "completeness",
    "condition_handling",
    "safety_preservation",
)
ALLOWED_FAILURE_LAYERS: tuple[FailureLayer, ...] = (
    "RETRIEVAL",
    "RANKING",
    "CONTEXT_SELECTION",
    "GENERATION",
    "EVALUATOR",
    "DATASET",
    "NONE",
    "UNCERTAIN",
)


class HumanAdjudicationRecord(BaseModel):
    """Final human decision kept separate from deterministic evaluator checks."""

    case_id: str
    groundedness: int = Field(ge=0, le=2)
    correctness: int = Field(ge=0, le=2)
    completeness: int = Field(ge=0, le=2)
    condition_handling: int = Field(ge=0, le=2)
    safety_preservation: int = Field(ge=0, le=2)
    unsupported_claim: bool
    critical_safety_omission: bool
    primary_failure_layer: FailureLayer
    secondary_failure_layer: FailureLayer | None = None
    failure_labels: list[str] = Field(default_factory=list)
    evaluator_diagnostics: list[str] = Field(default_factory=list)
    rationale: str
    adjudication_status: AdjudicationStatus = "final"
    post_hoc_root_cause_evidence_audit: str | None = None


class HumanAdjudicationSource(BaseModel):
    """Versioned input record for final human adjudication decisions."""

    adjudication_version: str
    source_baseline_path: str
    records: list[HumanAdjudicationRecord]


class AdjudicatedAnswerCase(AnswerCaseResult):
    """Frozen answer result with populated review fields and extended attribution."""

    human_adjudication: HumanAdjudicationRecord


class HumanAdjudicatedRun(BaseModel):
    """Derived artifact; the original formal answer baseline remains unchanged."""

    generated_at: str
    adjudication_version: str
    source_baseline_path: str
    source_baseline_generated_at: str
    case_count: int
    semantics_version: str
    config: dict[str, Any] = Field(default_factory=dict)
    automated_summary: dict[str, float | int | None] = Field(default_factory=dict)
    human_summary: dict[str, Any] = Field(default_factory=dict)
    results: list[AdjudicatedAnswerCase] = Field(default_factory=list)


def load_human_adjudication_source(path: str | Path) -> HumanAdjudicationSource:
    source_path = Path(path)
    try:
        source = HumanAdjudicationSource.model_validate_json(
            source_path.read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Invalid human adjudication source: {source_path}") from exc

    case_ids = [record.case_id for record in source.records]
    duplicates = _duplicates(case_ids)
    if duplicates:
        raise ValueError(f"Duplicate human adjudication case ids: {sorted(duplicates)}")
    return source


def build_human_adjudicated_run(
    baseline: AnswerEvaluationRun,
    *,
    source_baseline_path: str,
    adjudication_source: HumanAdjudicationSource,
) -> HumanAdjudicatedRun:
    """Attach final human decisions without changing the source baseline artifact."""

    baseline_ids = [result.case_id for result in baseline.results]
    decisions = {record.case_id: record for record in adjudication_source.records}
    baseline_id_set = set(baseline_ids)
    decision_id_set = set(decisions)
    missing = baseline_id_set - decision_id_set
    extra = decision_id_set - baseline_id_set
    if missing or extra:
        raise ValueError(
            "Human adjudication records do not match baseline cases: "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )

    adjudicated_results = [
        _adjudicate_result(result, decisions[result.case_id]) for result in baseline.results
    ]
    human_summary = summarize_human_adjudications(adjudicated_results)
    return HumanAdjudicatedRun(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        adjudication_version=adjudication_source.adjudication_version,
        source_baseline_path=source_baseline_path,
        source_baseline_generated_at=baseline.generated_at,
        case_count=len(adjudicated_results),
        semantics_version=baseline.semantics_version,
        config=baseline.config,
        automated_summary=baseline.summary,
        human_summary=human_summary,
        results=adjudicated_results,
    )


def summarize_human_adjudications(
    results: list[AdjudicatedAnswerCase],
) -> dict[str, Any]:
    """Calculate V4.5-C aggregate values from final human decisions."""

    reviews = [result.human_adjudication for result in results]
    distributions = {
        dimension: {
            str(score): sum(getattr(review, dimension) == score for review in reviews)
            for score in (0, 1, 2)
        }
        for dimension in HUMAN_SCORE_DIMENSIONS
    }
    means = {
        dimension: (mean(getattr(review, dimension) for review in reviews) if reviews else None)
        for dimension in HUMAN_SCORE_DIMENSIONS
    }
    full_pass_count = sum(_is_human_full_pass(review) for review in reviews)
    severe_failure_count = sum(_is_severe_failure(review) for review in reviews)
    denominator = len(reviews)
    layer_counter = Counter(review.primary_failure_layer for review in reviews)
    label_counter = Counter(
        label for review in reviews for label in review.failure_labels
    )
    diagnostic_counter = Counter(
        diagnostic for review in reviews for diagnostic in review.evaluator_diagnostics
    )
    return {
        "case_count": denominator,
        "dimension_score_distribution": distributions,
        "dimension_mean": means,
        "human_full_pass_definition": (
            "所有五个维度均为 2，且 unsupported_claim=false，"
            "且 critical_safety_omission=false"
        ),
        "human_full_pass_count": full_pass_count,
        "human_full_pass_rate": _rate(full_pass_count, denominator),
        "severe_failure_definition": (
            "correctness=0 或 groundedness=0 或 safety_preservation=0，"
            "或 critical_safety_omission=true"
        ),
        "severe_failure_count": severe_failure_count,
        "severe_failure_rate": _rate(severe_failure_count, denominator),
        "unsupported_claim_count": sum(review.unsupported_claim for review in reviews),
        "unsupported_claim_rate": _rate(
            sum(review.unsupported_claim for review in reviews), denominator
        ),
        "critical_safety_omission_count": sum(
            review.critical_safety_omission for review in reviews
        ),
        "critical_safety_omission_rate": _rate(
            sum(review.critical_safety_omission for review in reviews), denominator
        ),
        "primary_failure_layer_distribution": {
            layer: layer_counter.get(layer, 0) for layer in ALLOWED_FAILURE_LAYERS
        },
        "failure_label_frequency": dict(sorted(label_counter.items())),
        "evaluator_diagnostic_frequency": dict(sorted(diagnostic_counter.items())),
    }


def render_human_adjudication_markdown(run: HumanAdjudicatedRun) -> str:
    """Render the V4.5-C Chinese consolidation report."""

    summary = run.human_summary
    lines = [
        "# V4.5-C 人工裁决汇总与失败分类报告",
        "",
        "## 1. 范围与冻结实验身份",
        "",
        "本报告汇总 V4.5-B 的最终人工裁决；它是对冻结 V4.4 基线的派生审计产物，"
        "不修改原始答案、检索行为、V4.3 评测语义或 answer-eval contract。",
        "",
        f"- 源基线：`{run.source_baseline_path}`",
        f"- 源基线生成时间：{run.source_baseline_generated_at}",
        f"- 人工裁决版本：`{run.adjudication_version}`",
        f"- 评测语义版本：`{run.semantics_version}`",
        f"- case 数量：{run.case_count}（11 条正例，1 条 hard-negative）",
        f"- 检索配置：{_display(run.config.get('retrieval_mode'))}；"
        f"rerank={_display(run.config.get('rerank_enabled'))}；"
        f"top_k={_display(run.config.get('top_k'))}",
        f"- Context selection：{_display(run.config.get('metadata_context_selection_enabled'))}；"
        f"neighbor expansion={_display(run.config.get('neighbor_expansion_enabled'))}",
        f"- Context budget：max_contexts={_display(run.config.get('max_contexts'))}；"
        f"max_context_chars={_display(run.config.get('max_context_chars'))}",
        f"- 模型：`{_display(run.config.get('llm_model'))}`；"
        f"Ollama={_display(run.config.get('ollama_version'))}；"
        f"digest=`{_display(run.config.get('ollama_model_digest'))}`",
        "- 生成参数：stream=false；temperature/seed/options 均未显式设置，"
        "因此严格可复现性仍为 **NO**。",
        "",
        "## 2. 人工裁决方法",
        "",
        "人工分数是本阶段唯一的 answer-quality 结论来源。自动检查、术语覆盖和结构命中"
        "只保留为诊断字段，不能覆盖人工裁决。Groundedness 审核仅使用模型实际可见的"
        "`prompt_evidence`；未进入 prompt 的 citation、索引内容或外部知识均不作为证据。",
        "",
        "## 3. 12 条 Case 人工裁决汇总",
        "",
        "| case_id | 五维评分 G/C/Co/Ch/S | unsupported | critical safety omission | 主要层 | 失败标签 | 评估器诊断 | 裁决摘要 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in run.results:
        review = result.human_adjudication
        scores = "/".join(
            str(getattr(review, dimension)) for dimension in HUMAN_SCORE_DIMENSIONS
        )
        labels = "、".join(review.failure_labels) if review.failure_labels else "无"
        diagnostics = (
            "、".join(review.evaluator_diagnostics)
            if review.evaluator_diagnostics
            else "无"
        )
        lines.append(
            "| "
            f"`{result.case_id}` | {scores} | {_bool_text(review.unsupported_claim)} | "
            f"{_bool_text(review.critical_safety_omission)} | {review.primary_failure_layer} | "
            f"{labels} | {diagnostics} | {review.rationale} |"
        )

    lines.extend(
        [
            "",
            "说明：G=groundedness，C=correctness，Co=completeness，"
            "Ch=condition handling，S=safety preservation；各项取值为 0/1/2。",
            "",
            "## 4. 人工聚合指标",
            "",
            "### 4.1 各维度分布与均值",
            "",
            "| 维度 | 0 分 | 1 分 | 2 分 | 平均分 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    distributions = summary["dimension_score_distribution"]
    means = summary["dimension_mean"]
    for dimension in HUMAN_SCORE_DIMENSIONS:
        lines.append(
            f"| {dimension} | {distributions[dimension]['0']} | "
            f"{distributions[dimension]['1']} | {distributions[dimension]['2']} | "
            f"{means[dimension]:.4f} |"
        )
    lines.extend(
        [
            "",
            "### 4.2 通过与严重失败",
            "",
            f"- Human Full Pass 定义：{summary['human_full_pass_definition']}。",
            f"- Human Full Pass：{summary['human_full_pass_count']}/{summary['case_count']} "
            f"（{summary['human_full_pass_rate']:.2%}）。",
            f"- Severe failure 定义：{summary['severe_failure_definition']}。",
            f"- Severe failure：{summary['severe_failure_count']}/{summary['case_count']} "
            f"（{summary['severe_failure_rate']:.2%}）。",
            f"- Unsupported claim：{summary['unsupported_claim_count']}/{summary['case_count']} "
            f"（{summary['unsupported_claim_rate']:.2%}）。",
            f"- Critical safety omission：{summary['critical_safety_omission_count']}/"
            f"{summary['case_count']}（{summary['critical_safety_omission_rate']:.2%}）。",
            "",
            "## 5. 失败分类与根因分析",
            "",
            "### 5.1 主要失败层分布",
            "",
            "| 层级 | case 数 |",
            "| --- | ---: |",
        ]
    )
    for layer, count in summary["primary_failure_layer_distribution"].items():
        lines.append(f"| {layer} | {count} |")
    lines.extend(["", "### 5.2 失败标签频次", "", "| 标签 | 次数 |", "| --- | ---: |"])
    for label, count in summary["failure_label_frequency"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            "### 5.3 根因与症状必须分开理解",
            "",
            "- **检索失败**：`epb_enable_release_answer_001` 的正常启用 Evidence 未进入模型上下文；"
            "这是 complementary-evidence 缺失，不可被 ANY_OF Hit@K 掩盖。",
            "- **生成 grounding / 条件处理失败**：ABS 故障、遥控钥匙正常启动、"
            "EPB AUTO 与熄火后 EPB 释放等 case 的问题，主要表现为把通用或特殊条件"
            "错误推广为当前问题的确定步骤。",
            "- **Context contamination** 是促成条件，不等同于回答层症状；"
            "真正的回答层问题仍可能是 `GENERATION_GROUNDING_FAILURE` 或"
            "`CONDITION_HANDLING_FAILURE`。",
            "- **Unnecessary procedural expansion**：EPB AUTO 和超速 case 说明，"
            "即使核心结论正确，扩展无关程序也会降低答案边界清晰度；前者已影响人工评分，"
            "后者未降低五维评分。",
            "- **Safety-preservation failure**：ABS 故障与 EPB 启用/释放 case 各存在"
            "安全要求的遗漏或弱化；ABS 为本次唯一的 critical safety omission。",
            "",
            "## 6. 自动评估器分歧分析",
            "",
            "以下 `EVALUATOR_PROXY_FALSE_NEGATIVE` 是评估器诊断，不是 answer failure，"
            "不会单独使 Human Full Pass 失败。",
            "",
            "| 诊断 | 次数 | 相关 case | 说明 |",
            "| --- | ---: | --- | --- |",
        ]
    )
    diagnostics = summary["evaluator_diagnostic_frequency"]
    for diagnostic, count in diagnostics.items():
        case_ids = [
            result.case_id
            for result in run.results
            if diagnostic in result.human_adjudication.evaluator_diagnostics
        ]
        lines.append(
            f"| {diagnostic} | {count} | {', '.join(f'`{case_id}`' for case_id in case_ids)} | "
            "词汇近义表达或 section/subsection 结构代理与模型可见的 canonical Evidence 不一致。 |"
        )
    lines.extend(
        [
            "",
            "## 7. ABS 归因冲突的事后证据审计",
            "",
            "人工裁决的 primary failure layer 保持为 **GENERATION**，评分与标签不作改写。"
            "但对冻结 V4.4 `prompt_evidence` 的复核显示：其中只有 ABS 功能说明、"
            "故障警告灯以及通用故障处理流程；并没有 contract 要求的“立即在安全区域停车”"
            "这一专属安全指令。因此，事后根因证据审计与人工 primary attribution 存在冲突。",
            "",
            "该冲突被记录为 **需要显式协调**：人工 answer-quality 裁决仍然有效；"
            "但未来的根因归因不能把该 case 无条件视作纯 generation failure。",
            "",
            "## 8. 多 Gold Evidence 的检索指标限制",
            "",
            "冻结 V3.5 retrieval benchmark 对多个 gold evidence 使用 ANY_OF 语义："
            "TopK 命中任意一个 gold，Hit@K 即成功。`epb_enable_release_answer_001` 显示，"
            "当答案合同要求互补 Evidence（例如“启用”与“释放”两个独立事实）时，"
            "`Hit@K = 1` 并不意味着完整答案所需的所有 Evidence 都已进入上下文。",
            "",
            "这不是本阶段对冻结 retrieval evaluator 的修改。未来可候选引入：",
            "`GoldEvidenceCoverage@K = |TopK ∩ GoldEvidence| / |GoldEvidence|`，"
            "并在数据集显式区分 `ANY_OF`（等价证据）与 `ALL_OF` / complementary groups"
            "（共同需要的证据）。",
            "",
            "## 9. 已知限制",
            "",
            "- 本报告仅覆盖 12 条 development answer-evaluation cases，不能代表生产质量、"
            "跨车型表现或用户在线体验。",
            "- V4.4 使用 no-rerank 设置；本报告不比较 rerank on/off。",
            "- 未设置 generation temperature、seed 和 options，严格 generation reproducibility 仍为 NO。",
            "- elapsed time 是该次离线运行记录，不应解释为正式在线延迟指标。",
            "- 自动评估器代理分歧只被标记，不在本阶段修改 evaluator、normalization 或 contract。",
            "",
            "## 10. V4.5 结论与后续受控实验",
            "",
            "V4.5 已将 V4.4 的自动检查与最终人工裁决分离、固化并汇总。当前最显著的"
            "answer-level 风险是：在多个 Evidence 同时存在时，模型对适用条件和答案范围"
            "的保持不足；同时存在一个需要与 retrieval evidence audit 协调的 ABS 安全 case。",
            "",
            "后续实验应保持 V4.4 no-rerank 基线不变，并一次只改变一个变量。依据本次 taxonomy，"
            "优先候选为：",
            "",
            "1. 对 no-rerank 与 rerank 做受控的 answer-level A/B，观察条件保持、"
            "上下文污染和安全遗漏是否变化。",
            "2. 做 context-selection ablation，确认无关或特殊 Evidence 进入 prompt 是否是"
            "条件混合的必要前提。",
            "3. 单独验证“条件/例外保持”与“避免无必要程序扩写”的 generation contract；"
            "不得在本报告基础上直接修改 prompt。",
            "4. 将 complementary-evidence coverage 作为未来 retrieval/answer 联合评测的候选指标。",
            "5. 对已标记的 evaluator proxy false negative 建立独立、受控的 evaluator 改进实验。",
            "",
            "上述建议均为后续受控实验，不构成本阶段对 production RAG 的优化。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_human_adjudication_outputs(
    run: HumanAdjudicatedRun,
    *,
    markdown_path: str | Path,
    json_path: str | Path,
) -> tuple[Path, Path]:
    md_path = Path(markdown_path)
    structured_path = Path(json_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    structured_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_human_adjudication_markdown(run), encoding="utf-8")
    structured_path.write_text(
        json.dumps(run.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return md_path, structured_path


def _adjudicate_result(
    result: AnswerCaseResult,
    review: HumanAdjudicationRecord,
) -> AdjudicatedAnswerCase:
    populated_review = HumanAnswerReview(
        groundedness=review.groundedness,
        correctness=review.correctness,
        completeness=review.completeness,
        condition_handling=review.condition_handling,
        safety_preservation=review.safety_preservation,
        unsupported_claim=review.unsupported_claim,
        critical_safety_omission=review.critical_safety_omission,
        notes=review.rationale,
    )
    payload = result.model_dump()
    payload["human_review"] = populated_review.model_dump()
    payload["human_adjudication"] = review.model_dump()
    return AdjudicatedAnswerCase.model_validate(payload)


def _is_human_full_pass(review: HumanAdjudicationRecord) -> bool:
    return (
        all(getattr(review, dimension) == 2 for dimension in HUMAN_SCORE_DIMENSIONS)
        and not review.unsupported_claim
        and not review.critical_safety_omission
    )


def _is_severe_failure(review: HumanAdjudicationRecord) -> bool:
    return (
        review.correctness == 0
        or review.groundedness == 0
        or review.safety_preservation == 0
        or review.critical_safety_omission
    )


def _duplicates(values: list[str]) -> set[str]:
    counts = Counter(values)
    return {value for value, count in counts.items() if count > 1}


def _rate(count: int, denominator: int) -> float | None:
    return count / denominator if denominator else None


def _display(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"
