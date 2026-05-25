import streamlit as st


st.title("Auto Manual RAG Assistant")

question = st.text_input("请输入你的汽车使用问题")

if st.button("提交"):
    if question:
        st.write("占位答案：问答功能将在后续版本实现。")
    else:
        st.warning("请输入问题后再提交。")
