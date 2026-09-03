import os

import requests
import streamlit as st


st.set_page_config(page_title="Auto Manual RAG", layout="centered")

st.title("Auto Manual RAG")
st.caption("汽车用户手册本地问答")

api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

with st.sidebar:
    st.header("查询设置")
    retrieval_mode = st.selectbox("检索模式", ["hybrid", "dense", "bm25"], index=0)
    top_k = st.number_input("引用数量", min_value=1, max_value=20, value=5, step=1)
    show_debug = st.checkbox("显示检索详情", value=False)

question = st.text_input("请输入你的汽车使用问题")

if st.button("查询手册", type="primary", use_container_width=True):
    if question:
        try:
            with st.spinner("正在检索手册并生成回答..."):
                response = requests.post(
                    f"{api_base_url}/query",
                    json={
                        "question": question,
                        "top_k": int(top_k),
                        "retrieval_mode": retrieval_mode,
                    },
                    timeout=180,
                )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            st.error(f"请求后端失败：{exc}")
        else:
            st.subheader("回答")
            st.write(data.get("answer", ""))

            citations = data.get("citations", [])
            st.subheader(f"引用依据 ({len(citations)})")
            for index, citation in enumerate(citations, start=1):
                page = citation.get("page")
                section = citation.get("section") or "未标注章节"
                label = f"{index}. 第 {page if page is not None else '未知'} 页 · {section}"
                with st.expander(label, expanded=index == 1):
                    st.write(citation.get("quote") or "无可用摘录")
                    source_file = citation.get("source_file") or "N/A"
                    chapter = citation.get("chapter") or "N/A"
                    content_type = citation.get("content_type") or "normal"
                    risk_level = citation.get("risk_level") or "N/A"
                    st.caption(
                        f"来源：{source_file} · 章节：{chapter} · "
                        f"类型：{content_type} · 风险：{risk_level}"
                    )
                    if show_debug:
                        st.json(
                            {
                                "chunk_id": citation.get("chunk_id"),
                                "retrieval_source": citation.get("retrieval_source"),
                                "score": citation.get("score"),
                                "distance": citation.get("distance"),
                                "selection_score": citation.get("selection_score"),
                                "dense_rank": citation.get("dense_rank"),
                                "bm25_rank": citation.get("bm25_rank"),
                                "rrf_score": citation.get("rrf_score"),
                            }
                        )
    else:
        st.warning("请输入问题后再提交。")
