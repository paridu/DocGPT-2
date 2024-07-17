from openai import OpenAI
import streamlit as st
import os
from PIL import Image
import base64
from mimetypes import guess_type

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def reset():
    st.session_state.messages = [{
        "role":
        "system",
        "content":
        """
        As a healthcare assistant, your role is to assist users with their health-related queries, offering guidance and support as needed. When interacting with users, remember to respond in the same language that they use, ensuring clear communication. Your goal is to diagnose the patient with a specific condition based on the symptoms provided and explain it in simple terms for easy understanding.
        
        If the user's symptoms are vague, feel free to ask more questions to narrow down the diagnosis, unless the user specifically seeks pain relief and not a detailed diagnosis. After diagnosing the condition, recommend medications if applicable, or provide home remedies if medications are not readily available or accessible to the user.
        
        In case the patient sounds worried, it's important to offer empathy and reassurance in your response. Additionally, be prepared for users to upload images of their injuries or pills. When describing the images, consider the symptoms mentioned, provide a concise assessment of the situation, explain the consequences, and offer guidance on the next steps to take.
        
        If the user uploads images of pills, describe how often they should be taken, and if necessary, translate the instructions into their native language to ensure clear understanding and compliance. Remember to adjust your responses based on the information provided by the user, offering tailored support and recommendations throughout the interaction.
        """
    }]
    img_prompt = None

bc = st.get_option("theme.backgroundColor")
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
        position: sticky;
        top: 2rem;
        z-index: 999;
        width: 100%;        
        background-color: """ + bc + """;
    }
    .fixed-header {
        """ + bc + """
    }
</style>
    """,
            unsafe_allow_html=True)

header = st.container()
header.title("DocGPT - Healthcare Assistant")
header.write("""<div class='fixed-header'>""", unsafe_allow_html=True)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    reset()

with header:
    button_row = st.columns([30, 7], vertical_alignment="center")
    with button_row[0]:
        img_prompt = st.file_uploader('', type=["jpg", "jpeg", "png"])
    with button_row[1]:
        if st.button("Clear Chat"):
            reset()
header.write("""</div>""", unsafe_allow_html=True)


for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
                st.markdown(message["content"])

prompt = st.chat_input("Ask me anything!")


def encode_image(image):
    return base64.b64encode(image.read()).decode('utf-8')

base64_image = None 

if img_prompt:
    base64_image = encode_image(img_prompt)
    img_type = img_prompt.type
    img_url = f"data:{img_type};base64,{base64_image}"

if prompt or img_prompt:
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
    elif img_prompt:
        st.session_state.messages.append({
            "role": "user", 
            "content": [
                {"type": "image_url", "image_url": {"url": img_url}}
            ]
        })
        st.session_state["openai_model"] = "gpt-4o"

    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        elif img_prompt:
            st.image(img_prompt, use_column_width='auto')

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

    if img_prompt:
        st.session_state.messages.pop(-2)
        st.session_state["openai_model"] = "gpt-3.5-turbo"