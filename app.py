import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Interviewer Chatbot", page_icon="💬")
st.title("AI Interviewer")


client=OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] ="gpt-4.1"

if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown =False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        """
        Say hello and choose your topic.
        """,
        icon ="👋"
    )

    if not st.session_state.messages:
        st.session_state.messages = [{"role":"system", "content": f"You are an interviewer. You are interviewing a user about a topic of their choice.The interviewee chooses a topic. Use these details to create three to five sequential questions.Ask each questions individually, creating a conversational flow rather than presenting all the questions simultaneously."}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 6:
        if prompt :=st.chat_input("Type your answer"):
            st.session_state.messages.append({"role":"user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 5:
                with st.chat_message("assistant"):
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
            st.session_state.user_message_count+=1  

    if st.session_state.user_message_count>=5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback..")      