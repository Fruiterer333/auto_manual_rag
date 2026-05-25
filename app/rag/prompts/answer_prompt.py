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
1. 只能基于提供的手册片段回答问题。
2. 如果上下文中没有依据，回答“我没有在手册中找到可靠依据”。
3. 不要编造车辆功能、页码或引用。
4. 对驾驶安全、制动、高压、充电、儿童安全、气囊等问题保持谨慎。
5. 使用中文回答。

手册片段：
{context}

用户问题：
{question}

请给出回答：
""".strip()
