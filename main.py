import streamlit as st
import os
import base64
from openai import OpenAI
from streamlit.elements.image import UseColumnWith
from streamlit_mic_recorder import speech_to_text
from streamlit_geolocation import streamlit_geolocation
from streamlit_extras.stylable_container import stylable_container

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
sys_prompt = open("prompt.txt").read()


def clear_chat():
    st.session_state.current_session = [{"role": "system", "content": sys_prompt}]
    st.session_state.my_stt_output = None
    # st.rerun()


def initialize_session():
    st.session_state.header = st.container()
    st.session_state.chat_container = stylable_container("chatContainer",
        css_styles="""
        height: 5000px;
    """)
    st.session_state.input_container = st.container()
    # stylable_container("inputContainer",
    #     css_styles=[
    #         "position: sticky;", "bottom: 1rem;",
    #         "z-index: 999;", "width: 100%;"
    #         "background-color: #feffff"
    #     ])
    
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = dict()
        
    if "current_session" not in st.session_state:
        st.session_state.current_session = []
        clear_chat()

    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []



def encode_image_url(image):
    base64_image = base64.b64encode(image.read()).decode('utf-8')
    img_type = image.type
    return f"data:{img_type};base64,{base64_image}"


def speech_to_text_callback():
    if st.session_state.my_stt_output:
        st.write(st.session_state.my_stt_output)


def save_current_chat():
    sessions = st.session_state.chat_sessions
    curr_session = st.session_state.current_session
    if len(curr_session) > 1:
        title = curr_session[1]["content"]
        sessions[title] = curr_session
        

def load_chat(session):
    if session != st.session_state.current_session:
        save_current_chat()
        with st.session_state.chat_container:
            for message in session[1:]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        st.session_state.curr_session = session

def delete_current_chat():
    if len(st.session_state.current_session) > 1:
        st.session_state.chat_sessions.pop(st.session_state.current_session[1]["content"])
        update_sidebar()
        clear_chat()
    if not len(st.session_state.chat_sessions):
        clear_chat()


def update_sidebar():
    with st.sidebar:
        for title in st.session_state.chat_sessions:
            if st.button(title, key=title, type='primary'):
                load_chat(st.session_state.chat_sessions[title])

def main():
    with st.sidebar:
        with stylable_container("deleteChat",
                                css_styles=[
                                    """
    button{background-color:#A3CEF1}
    """, """
    button:hover{background-color:#6096BA; color:red; border-color:transparent;}
    """, """button:active{color:white; background-color:red}
    """
                                ]):
            if st.button("Delete current chat"):
                delete_current_chat()

                
        with stylable_container("createChat",
                                css_styles=[
                                    """
        button{background-color:#A3CEF1}
        """, """
        button:hover{background-color:#6096BA; color:red; border-color:transparent;}
        """, """button:active{color:white; background-color:red}
        """
                                ]):
            if st.button("Create new chat"):
                save_current_chat()
                clear_chat()
    update_sidebar()
        

    st.markdown(
        """<style>.eeusbqq4:nth-child(odd){background-color:#6096BA} .eeusbqq4:nth-child(even){background-color:#A3CEF1}</style>""",
        unsafe_allow_html=True)

    
    st.markdown(f"""
    <style>
        div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {{
            position: sticky;
            top: 1rem;
            z-index: 999;
            width: 100%;        
            background: #feffff;
        }}

        .e1f1d6gn5{{
        background-color: #feffff;
        }}
    </style>
        """,
                unsafe_allow_html=True)
    header = st.session_state.header
    header.write("""<div class='fixed-header'>""", unsafe_allow_html=True)

    with header:
        logo_columns = st.columns([5, 25, 5])
        with logo_columns[1]:
            with stylable_container(
                    "logo",
                    css_styles="""button[title="View fullscreen"]{
            visibility: hidden;}"""):
                st.image('assets/logo.png', use_column_width=True)
    header.write("""</div>""", unsafe_allow_html=True)

    for message in st.session_state.current_session:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with st.session_state.chat_container:
        if prompt or img_prompt:
            if prompt:
                st.session_state.current_session.append({
                    "role": "user",
                    "content": prompt
                })
            elif img_prompt:
                st.session_state.current_session.append({
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
                    st.markdown("Uploaded image")
            with st.spinner('Processing...'), st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[{
                            "role": m["role"],
                            "content": m["content"]
                        } for m in st.session_state.current_session],
                        stream=True,
                    )
                    response = st.write_stream(stream)
            st.session_state.current_session.append({
                "role": "assistant",
                "content": response
            })
            save_current_chat()
            if len(st.session_state.current_session) == 3:
                update_sidebar()
            if img_prompt:
                st.session_state.current_session.pop(-2)
                st.session_state["openai_model"] = "gpt-3.5-turbo"


    img_prompt = st.file_uploader('', type=["jpg", "jpeg", "png"])
    if img_prompt:
        st.write("Uploaded Image")
        st.image(img_prompt, use_column_width='auto')
        img_url = encode_image_url(img_prompt)
    
    
    st.markdown(
        """<style>.eeusbqq4:nth-child(odd){background-color:#6096BA} .eeusbqq4:nth-child(even){background-color:#A3CEF1}</style>""",
        unsafe_allow_html=True)
    
    st.markdown(f"""
    <style>
        div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {{
            position: sticky;
            bottom: 1rem;
            z-index: 999;
            width: 100%;        
            background: #feffff;
        }}
    
        .e1f1d6gn5{{
        background-color: #feffff;
        }}
    </style>
        """,
                unsafe_allow_html=True)
    input_container = st.session_state.input_container
    input_container.write("""<div class='fixed-header'>""", unsafe_allow_html=True)
    
    
    with st.session_state.input_container:
        input_cols = st.columns((12, 1))
        with input_cols[0]:
            prompt = st.chat_input("What is wrong?")
    
        with input_cols[1]:
            with st.spinner('Processing...'):
                stt = speech_to_text("🎤",
                                     "⏹️",
                                     language='en',
                                     key='my_stt',
                                     callback=speech_to_text_callback,
                                     just_once=True)
            if st.session_state.my_stt_output:
                prompt = st.session_state.my_stt_output
if __name__ == "__main__":
    initialize_session()
    main()
