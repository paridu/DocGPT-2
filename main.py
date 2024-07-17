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


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

base64_image = None 

if img_prompt:
    base64_image = encode_image(img_prompt)

if prompt or img_prompt:
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    elif img_prompt:
        st.session_state.messages.append({"role": "user", 
                                          "content":[
                                          {
                                              "type": "text",
                                              "text": "Describe this picture:"
                                          },
                                          {
                                              "type": "image_url",
                                              "image_url": {
                                                  "url": f"data:image/jpeg;base64{base64_image}"
                                              }
                                          }] 
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