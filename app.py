import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
import json
from datetime import datetime
from textblob import TextBlob
from collections import Counter
import re
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')


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
if "interview_saved" not in st.session_state:
    st.session_state.interview_saved = False

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

    if st.session_state.user_message_count>5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback..") 

if st.session_state.feedback_shown:
    st.subheader("Feedback")
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    feedback_completion = feedback_client.chat.completions.create(
        model = "gpt-4.1",
        messages=[
            {"role":"system", "content": """You are a helpful tool that provides feedback based on an interviewee performance and that provides a summary of the user's responses like themes, sentiment, key points.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overall Score: //Your score
             Feedback: //Here you put your feedback
             Summary: //The summary of the user's responses with the themes, sentiment and key points
             Give only the feedback and summary do not ask any addiotional questions.
             """
            },
            {"role":"user", "content": f"This is the interview you need to evaluate. You are only a tool and shouldn't engage in covnersation:{conversation_history}"}
        ]
    )     

    st.write(feedback_completion.choices[0].message.content)

    st.divider()
    st.subheader("NLP Analysis")
    user_responses=" ".join([msg['content'] for msg in st.session_state.messages if msg['role'] =='user'])

    bl=TextBlob(user_responses)
    sentiment_score = bl.sentiment.polarity

    st.metric("Sentiment Score", f"{sentiment_score:.2f}",
                help= "Range: -1 (negative) to 1 (positive)")
    if sentiment_score>0.1:
        st.success("Positive sentiment")
    elif sentiment_score <-0.1:
        st.error("Negative sentiment")
    else:
        st.info("Neutral sentiment")

    st.write("Top Keywords:")
    words=re.findall(r'\b[a-zA-Z]{4,}\b', user_responses.lower())
    stop_words = stopwords.words('english')
    words=[word for word in words if word not in stop_words ]
    keywords=Counter(words).most_common(10)

    if keywords:
        for i, (word, count) in enumerate(keywords,1):
            st.write(f"{i}.**{word.capitalize()}** - mentioned {count} times")
    else:
        st.write("No significant words")


    if st.session_state.feedback_shown and not st.session_state.interview_saved:
        interview_data ={
            "timestamp":datetime.now().isoformat(),
            "messages":st.session_state.messages,
            "feedback":feedback_completion.choices[0].message.content
        }
        filename= f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(interview_data, f, ensure_ascii = False, indent=4)

        st.session_state.interview_saved = True
    
    if st.button("Restart interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")