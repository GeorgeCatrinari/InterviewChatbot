import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Interviewer Chatbot", page_icon="💬")
st.title("AI Interviewer")

client=OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] ="gpt-4.1"

if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt :=st.chat_input("Type your answer"):
    st.session_state.messages.append({"role":"user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("ai"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role":"assistant", "content":response})        