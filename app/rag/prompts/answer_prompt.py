from dataclasses import dataclass

from app.data.schemas.models import Chunk


DEFAULT_MAX_CONTEXTS = 5
DEFAULT_MAX_CONTEXT_CHARS = 6000
TRUNCATED_MARKER = "[TRUNCATED]"


@dataclass(frozen=True)
class _PromptEvidence:
    chunk: Chunk
    content: str
    truncated: bool = False


def build_answer_prompt(
    question: str,
    chunks: list[Chunk],
    *,
    max_contexts: int = DEFAULT_MAX_CONTEXTS,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
) -> str:
    evidences = _select_prompt_evidence(
        chunks,
        max_contexts=max_contexts,
        max_chars=max_context_chars,
    )
    context = "\n\n".join(
        _format_evidence(evidence, f"E{index}")
        for index, evidence in enumerate(evidences, start=1)
    )

    return f"""
你是汽车用户手册问答助手。

回答规则：
1. 仅依据下方 Evidence 回答。不得使用外部知识补充手册未明确给出的功能、步骤、条件或结论；所有操作性建议必须能在 Evidence 中找到直接依据。
2. 如果现有 Evidence 不足以可靠回答，直接说明“我没有在手册中找到可靠依据”，不要猜测。
3. 对警告、禁止、必须、安全条件和高风险操作，不得省略或弱化。涉及制动、高压、充电、气囊、儿童安全、故障等问题时尤其如此。
4. 多条 Evidence 结论不同时，先判断是否由于车辆状态、功能状态、模式、环境或其他适用条件不同：条件差异应分别说明；一般规则与特殊规则并存时应说明两者关系；同一条件下真正冲突且无法根据手册消解时，不要自行裁决，应说明无法确定唯一结论。
5. 用户询问“有哪些”“注意事项”“检查什么”“怎么做”“如何”等问题时，如果 Evidence 中存在直接相关列表，应优先按手册结构整理，并尽量覆盖直接相关条目。
6. 使用中文直接面向车主回答。Evidence ID 仅用于内部判断，最终回答不得输出 E1/E2、Evidence ID、CONTEXT、source id 等内部标识；不要逐字复制大段原文。

Evidence:
{context or "N/A"}

用户问题：
{question}

请给出回答：
""".strip()


def _format_evidence(evidence: _PromptEvidence, evidence_id: str) -> str:
    chunk = evidence.chunk
    page = chunk.page if chunk.page is not None else "N/A"
    subsection = _display_value(chunk.subsection or chunk.metadata.get("subsection"))
    lines = [
        f"[EVIDENCE {evidence_id}]",
        f"page: {page}",
        f"chapter: {_display_value(chunk.chapter)}",
        f"section: {_display_value(chunk.section)}",
        f"subsection: {subsection}",
        f"heading_path: {_format_heading_path(chunk)}",
        f"content_type: {chunk.content_type or 'normal'}",
        "content:",
        evidence.content,
    ]
    if evidence.truncated:
        lines.append("truncated: true")
    lines.append("[/EVIDENCE]")
    return "\n".join(lines)


def _format_heading_path(chunk: Chunk) -> str:
    value = chunk.metadata.get("heading_path")
    if isinstance(value, list):
        headings = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        headings = [part.strip() for part in value.split(">") if part.strip()]
    else:
        headings = [
            heading
            for heading in (chunk.chapter, chunk.section, chunk.subsection)
            if heading
        ]
    return " > ".join(headings) if headings else "N/A"


def _select_prompt_evidence(
    chunks: list[Chunk],
    *,
    max_contexts: int,
    max_chars: int,
) -> list[_PromptEvidence]:
    if max_contexts <= 0 or max_chars <= 0:
        return []

    selected: list[_PromptEvidence] = []
    total_chars = 0
    for chunk in chunks[:max_contexts]:
        content = chunk.text.strip()
        content_length = len(content)
        if total_chars + content_length <= max_chars:
            selected.append(_PromptEvidence(chunk=chunk, content=content))
            total_chars += content_length
            continue

        if not selected:
            selected.append(
                _PromptEvidence(
                    chunk=chunk,
                    content=_truncate_content(content, max_chars),
                    truncated=True,
                )
            )
        break
    return selected


def _truncate_content(content: str, max_chars: int) -> str:
    marker = f"\n{TRUNCATED_MARKER}"
    if max_chars <= len(TRUNCATED_MARKER):
        return TRUNCATED_MARKER[:max_chars]
    available_chars = max_chars - len(marker)
    return f"{content[:available_chars].rstrip()}{marker}"


def _display_value(value: object) -> str:
    if value is None or value == "":
        return "N/A"
    return str(value)
