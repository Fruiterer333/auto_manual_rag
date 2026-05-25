from app.data.schemas.models import Chunk


def build_answer_prompt(question: str, chunks: list[Chunk]) -> str:
    context_parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        page = chunk.page if chunk.page is not None else "未知"
        context_parts.append(
            f"[片段 {index} | page={page} | chunk_id={chunk.chunk_id}]\n{chunk.text}"
        )

    context = "\n\n".join(context_parts)
    return f"""
你是汽车用户手册问答助手。请严格遵守以下规则：
1. 回答必须严格基于提供的手册片段。
2. 回答中的每一条操作建议，都必须能在手册片段中找到直接依据。
3. 不要根据常识、经验或外部知识补充手册中没有明确出现的步骤。
4. 不要编造车辆功能、页码、章节或引用。
5. 如果上下文依据不足，回答“我没有在手册中找到可靠依据。”
6. 对驾驶安全、制动、高压系统、充电、儿童安全、气囊、故障灯等高风险问题，应优先保持保守表达。
7. 使用中文回答。

手册片段：
{context}

用户问题：
{question}

请给出回答：
""".strip()
