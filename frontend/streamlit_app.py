import os

import requests
import streamlit as st


st.title("Auto Manual RAG Assistant")

question = st.text_input("请输入你的汽车使用问题")
top_k = st.number_input("top_k", min_value=1, max_value=20, value=5, step=1)
retrieval_mode = st.selectbox("检索模式", ["hybrid", "dense", "bm25"], index=0)
api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

if st.button("提交"):
    if question:
        try:
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

            st.subheader("引用")
            for citation in data.get("citations", []):
                score = citation.get("score")
                distance = citation.get("distance")
                selection_score = citation.get("selection_score")
                is_expanded_neighbor = citation.get("is_expanded_neighbor")
                retrieval_source = citation.get("retrieval_source")
                dense_rank = citation.get("dense_rank")
                bm25_rank = citation.get("bm25_rank")
                rrf_score = citation.get("rrf_score")
                score_text = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"
                distance_text = (
                    f"{distance:.4f}" if isinstance(distance, (int, float)) else "N/A"
                )
                selection_score_text = (
                    f"{selection_score:.4f}"
                    if isinstance(selection_score, (int, float))
                    else "N/A"
                )
                st.markdown(
                    f"- score={score_text} | distance={distance_text} | "
                    f"selection_score={selection_score_text} | "
                    f"retrieval_source={retrieval_source or 'N/A'} | "
                    f"dense_rank={dense_rank or 'N/A'} | "
                    f"bm25_rank={bm25_rank or 'N/A'} | "
                    f"rrf_score={rrf_score if rrf_score is not None else 'N/A'} | "
                    f"expanded_neighbor={is_expanded_neighbor or False} | "
                    f"page={citation.get('page')} | "
                    f"chapter={citation.get('chapter') or 'N/A'} | "
                    f"section={citation.get('section') or 'N/A'} | "
                    f"content_type={citation.get('content_type') or 'N/A'} | "
                    f"risk_level={citation.get('risk_level') or 'N/A'}  \n"
                    f"  {citation.get('quote')}"
                )
    else:
        st.warning("请输入问题后再提交。")
