import streamlit as st
import os
import base64
from openai import OpenAI
from streamlit.elements.image import UseColumnWith
from streamlit_mic_recorder import speech_to_text
from streamlit_geolocation import streamlit_geolocation

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
sys_prompt = open("prompt.txt").read()

def clear_chat():
    st.session_state.messages = [{
        "role":
        "system",
        "content": sys_prompt
    }]
    img_prompt = None
    st.session_state.my_stt_output = None

def initialize_session():
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"
    
    if "messages" not in st.session_state:
        clear_chat()
    
    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []

def encode_image_url(image):
    base64_image = base64.b64encode(image.read()).decode('utf-8')
    img_type = img_prompt.type
    return f"data:{img_type};base64,{base64_image}"

def speech_to_text_callback():
    if st.session_state.my_stt_output:
        st.write(st.session_state.my_stt_output)

def main():
    bc = st.get_option("theme.backgroundColor")
    st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
            position: sticky;
            top: 1rem;
            z-index: 999;
            width: 100%;        
            background-color: """ + bc + """;
        }
    </style>
        """,
                unsafe_allow_html=True)

    header = st.container()
    header.write("""<div class='fixed-header'>""", unsafe_allow_html=True)

    with header:
        logo_columns = st.columns([5, 25, 5])
        with logo_columns[1]:
            st.image('assets/docgptLogo.png', use_column_width=True)
    header.write("""</div>""", unsafe_allow_html=True)

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    prompt = st.chat_input("Ask me anything!")

    with st.sidebar:
        if st.button("Clear Chat"):
            clear_chat()

        with st.spinner('Processing...'):
            stt = speech_to_text(language='en',
                                 key='my_stt',
                                 callback=speech_to_text_callback,
                                 just_once=True)
            text_container = st.container()
            with text_container:
                if stt:
                    st.write("You said: \n")
                    st.write(stt)
                else:
                    st.write("No speech detected")
        if st.session_state.my_stt_output:
            prompt = st.session_state.my_stt_output

        img_prompt = st.file_uploader('', type=["jpg", "jpeg", "png"])
        if img_prompt:
            st.write("Uploaded Image")
            st.image(img_prompt, use_column_width='auto')
            img_url = encode_image_url(img_prompt)
    
    if prompt or img_prompt:
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
        elif img_prompt:
            st.session_state.messages.append({
                "role":
                "user",
                "content": [{
                    "type": "image_url",
                    "image_url": {
                        "url": img_url
                    }
                }]
            })
            st.session_state.uploaded_images.append(img_prompt)
            st.session_state["openai_model"] = "gpt-4o"
    
        with st.chat_message("user"):
            if prompt:
                st.markdown(prompt)
            if img_prompt:
                st.markdown("User uploaded an image")
    
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


if __name__ == "__main__":
    initialize_session()
    main()