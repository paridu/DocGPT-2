from openai import OpenAI
import streamlit as st
import os


def reset():
    st.session_state.messages = [{
        "role":
        "system",
        "content":
        """
        You are a healthcare assistant. Based on the user's symptoms and conditions, provide a diagnosis if one is needed. Then recommend medications if they are applicable. If the patient states that they are at home or otherwise do not have access to medications, provide home remedies.
        If a diagnosis is needed, explain the condition in simple language that a layman can understand.
        If the patient sounds worried, write an empathetic and supportive message to provide reassurance.
        Use the previous messages provided by the patient / yourself in order to give a more informed response.
        The user may provide you with images or videos of their injuries. If so, please describe what you see in the image, what is happening to them, the consequences, and what actions to take. Please be compassionate when doing this and try to soothe the patient's pain.
        """
    }]


st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
        position: sticky;
        top: 2rem;
        background-color: #0e1117;
        z-index: 999;
        width: 100%;
    }
    .fixed-header {
    }
</style>
    """,
            unsafe_allow_html=True)

header = st.container()
header.title("DocGPT - Healthcare Assistant")
header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    reset()

with header:
    button_row = st.columns([38, 8])
    with button_row[1]:
        if st.button("Clear Chat"):
            reset()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{
                "role": m["role"],
                "content": m["content"]
            } for m in st.session_state.messages],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
