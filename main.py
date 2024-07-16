from openai import OpenAI
import streamlit as st
import os


def reset():
    st.session_state.messages = [{
        "role":
        "system",
        "content":
        """
        You are a healthcare assistant. 
        The user will ask you questions about their health.
        Try to diagnose the patient with a specific condition, and explain the condition in simple language that a layman can understand.
        If the symptoms given by the user are too vague, you can ask more questions to narrow down the diagnosis, unless the user just wants pain relief from their symptoms and not a proper diagnosis.
        After a diagnosis is made, recommend medications if they are applicable. You can provide home remedies only if the medications are not typical in a household OR if the user specifies they can't access them at the current time.
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
        z-index: 999;
        width: 100%;
    }
    .fixed-header {
    }
    div[data-testid="stVerticalBlock"] div:has(div.fixed-footer) {
        position: sticky;
        bottom: 7rem;
        z-index: 999;
        width: 100%;
    }
    .fixed-footer {
        border-bottom: 0px solid black;
        position: absolute;
        bottom: 0px;
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
    if message["role"] != "system":
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


footer = st.container()
footer.write("""<div class='fixed-footer'/>""", unsafe_allow_html=True)

with footer:
    uploaded_file = st.file_uploader('', type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.session_state.messages.append({"role": "user", "content": "User uploaded an image"})
        with st.chat_message("user"):
            st.image(uploaded_file, use_column_width=True)
st.markdown('</div>', unsafe_allow_html=True)