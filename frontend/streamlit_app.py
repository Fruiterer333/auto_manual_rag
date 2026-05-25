import os

import requests
import streamlit as st


st.title("Auto Manual RAG Assistant")

question = st.text_input("请输入你的汽车使用问题")
top_k = st.number_input("top_k", min_value=1, max_value=20, value=5, step=1)
api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

if st.button("提交"):
    if question:
        try:
            response = requests.post(
                f"{api_base_url}/query",
                json={"question": question, "top_k": int(top_k)},
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
                st.markdown(f"- page={citation.get('page')}  \n  {citation.get('quote')}")
    else:
        st.warning("请输入问题后再提交。")
