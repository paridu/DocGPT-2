import streamlit as st
import os
import base64
from openai import OpenAI
from streamlit.elements.image import UseColumnWith
from streamlit_mic_recorder import speech_to_text
from streamlit_extras.stylable_container import stylable_container
from streamlit_modal import Modal
from streamlit_js_eval import get_geolocation
import requests
from geopy.distance import geodesic
from streamlit_folium import folium_static
import folium
import time

GOOGLE_API_KEY = os.environ['GOOGLE_MAP_API']
NEARBY_SEARCH_URL = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = f"https://maps.googleapis.com/maps/api/place/details/json"
CLIENT = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
SYS_PROMPT = open('prompt.txt').read()
LOGO_PATH = 'assets/logo.png'


def clear_chat():
    st.session_state.current_session = [{
        "role": "system",
        "content": SYS_PROMPT
    }]
    st.session_state.stt_output = None
    st.session_state.current_session_title = ""


def initialize_session():
    st.session_state.header = st.container()
    st.session_state.chat_container = st.container(height=450, border=False)
    st.session_state.input_container = st.container()

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"

    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = dict()
    
    if "current_session" not in st.session_state:
        st.session_state.current_session = []
        clear_chat()

    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []

    if 'find_clinics_button_clicked' not in st.session_state:
        st.session_state.find_clinics_button_clicked = False

    if 'show_modal' not in st.session_state:
        st.session_state.show_modal = False

    if 'current_session_title' not in st.session_state:
        st.session_state.current_session_title = ""

    if 'titles_list' not in st.session_state:
        st.session_state.titles_list = []


def encode_image_url(image):
    base64_image = base64.b64encode(image.read()).decode('utf-8')
    img_type = image.type
    return f"data:{img_type};base64,{base64_image}"


def speech_to_text_callback():
    if st.session_state.stt_output:
        st.write(st.session_state.stt_output)


def save_current_chat():
    sessions = st.session_state.chat_sessions
    curr_session = st.session_state.current_session

    # key = generated title, value = chat session messages
    if len(curr_session) > 1:
        if not st.session_state.current_session_title:
            title_prompt = "Please generate a short, concise title based on the following message. Maximum of 30 characters, no quotation marks."
            first_user_message = curr_session[1]["content"]
            title = CLIENT.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[{
                    "role": "user",
                    "content": title_prompt + first_user_message
                }],
            ).choices[0].message.content
            st.session_state.current_session_title = title
            st.session_state.titles_list.append(title)
        else:
            title = st.session_state.current_session_title
        if not isinstance(title, list):
            sessions[title] = curr_session

def load_chat(session):
    if session != st.session_state.current_session:
        save_current_chat()
        # with st.session_state.chat_container:
        #     for message in session[1:]:
        #         with st.chat_message(message["role"]):
        #             st.markdown(message["content"])
        
        st.session_state.current_session = session
        key_to_swap = None
        for key, st_session in st.session_state.chat_sessions.items():
            if session == st_session:
                key_to_swap = key
                break
        st.session_state.current_session_title = key_to_swap


def delete_current_chat():
    key_to_delete = None
    for key, session in st.session_state.chat_sessions.items():
        if session == st.session_state.current_session:
            key_to_delete = key
            break
    
    st.session_state.titles_list.remove(key_to_delete)

    if key_to_delete:
        del st.session_state.chat_sessions[key_to_delete]
        success = st.success(f"Deleting session: {key_to_delete}")
        time.sleep(1.5)
        success.empty()
        update_sidebar()
        clear_chat()
    if not len(st.session_state.chat_sessions):
        clear_chat()


def update_sidebar():
    with st.sidebar:
        for title in st.session_state.chat_sessions:
            if st.button(title, key=title, type='secondary'):
                load_chat(st.session_state.chat_sessions[title])


def enter_details():
    with st.form(key="details_form"):
        st.markdown("Your information is kept private and will be :red[deleted] after swapping sessions.")
        gender = st.selectbox("Gender", ["Male", "Female"])
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        height = st.number_input("Height (cm)", min_value=0, step=1)
        weight = st.number_input("Weight (kg)", min_value=0, step=1)
        if st.form_submit_button(label="Submit details"):
            if age == 0 or height == 0 or weight == 0:
                st.error("Please ensure all fields are filled out correctly.")
            else:
                st.session_state.current_session[0] = {"role": "system",
                "content": SYS_PROMPT + f"""
                Keep in mind of the following details about the user, and use it to make a more informed diagnosis.
                Gender: {gender}
                Age: {age} years old
                Height: {height} cm
                Weight: {weight} kg
                """}
                st.success("Details submitted successfully!")

def get_nearest_clinics(lat, lon):
    params = {
        'location': f'{lat},{lon}',
        'keyword': 'clinic|medical center|health care|klinik|hospital',
        'rankby': 'distance',
        'opennow': 'true',
        'key': GOOGLE_API_KEY
    }
    response = requests.get(NEARBY_SEARCH_URL, params=params)
    data = response.json()
    clinics = []

    if 'results' in data and len(data['results']) > 0:
        for clinic in data['results']:
            place_id = clinic['place_id']
            detail_params = {
                'place_id': place_id,
                'fields': 'name,vicinity,geometry,opening_hours,photos',
                'key': GOOGLE_API_KEY
            }
            detail_response = requests.get(PLACE_DETAILS_URL,
                                           params=detail_params)
            detail_data = detail_response.json()
            if 'result' in detail_data:
                clinic_detail = detail_data['result']
                clinic_name = clinic_detail['name']
                clinic_address = clinic_detail.get('vicinity', 'N/A')
                clinic_coordinates = clinic_detail['geometry']['location']
                distance = geodesic(
                    (lat, lon),
                    (clinic_coordinates['lat'], clinic_coordinates['lng'])).km

                photos = clinic_detail.get('photos', [])

                photo_urls = []
                if photos:
                    for photo in photos[:2]:
                        photo_reference = photo['photo_reference']
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_API_KEY}"
                        photo_urls.append(photo_url)

                clinics.append({
                    'Name':
                    clinic_name,
                    'Address':
                    clinic_address,
                    'Coordinates':
                    (clinic_coordinates['lng'], clinic_coordinates['lat']),
                    'Distance':
                    distance,
                    'Photos':
                    photo_urls
                })

            if len(clinics) >= 5:
                break

    return clinics

# def check_nearest_clinics():
def add_sidebar_divider(text):
    st.sidebar.markdown(
        f"""
        <div style="display: flex; align-items: center; text-align: center;">
            <hr style="flex-grow: 1; height: 1px; border: none; background-color: #E0E0E0;"/>
            <span style="flex-shrink: 0; padding: 0 10px; font-size: 12px; color: #999999;">{text}</span>
            <hr style="flex-grow: 1; height: 1px; border: none; background-color: #E0E0E0;"/>
        </div>
        """,
        unsafe_allow_html=True,
    )

def main():
    st.markdown("""
        <style> 
        .eeusbqq4:nth-child(odd){background-color:#D9EEFF}
        .eeusbqq4:nth-child(even){background-color:white}
        .eeusbqq4:nth-last-child(1){background-color:white}
        div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
            position: sticky;
            bottom: 0rem;
            z-index: 999;
            width: 100%;        
            background: #feffff;
        }
        </style>
        """,
                unsafe_allow_html=True)
    st.markdown('''
        <style>
            div[data-testid="stAppViewBlockContainer"] {
                padding-top: 1.5rem;
                padding-bottom: 0px;
            }
            div[data-testid="stHorizontalBlock"] {
                padding-top: 1rem;
                padding-bottom: 0px;
            }
            e1f1d6gn2 {
                color: transparent;
            }
        </style>
        ''',
                unsafe_allow_html=True)

    ### SIDEBAR ###
    with st.sidebar:
        with st.popover(":blue[Enter your details]"):
            enter_details()
        find_clinics_button = st.button("Find nearby clinics", type='primary')
        if find_clinics_button:
            st.session_state.find_clinics_button_clicked = True
            st.session_state.show_modal = True
            # modal = Modal(key="clinics", title="Find nearby clinics")
            # with st.session_state.chat_container:
            #     with st.spinner('Searching...'):
            #         check_nearest_clinics()
        if st.button("Delete current chat", type='primary'):
            delete_current_chat()
        if st.button("Create new chat", type='primary'):
            save_current_chat()
            clear_chat()
        add_sidebar_divider("Chat sessions")
        
    update_sidebar()
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

    ### HEADER ###
    header = st.session_state.header
    header.write("""<div class='fixed-header'>""", unsafe_allow_html=True)

    with header:
        logo_columns = st.columns([10, 15, 10])
        with logo_columns[1]:
            with stylable_container(
                    "logo",
                    css_styles="""button[title="View fullscreen"]{
            visibility: hidden;}"""):
                st.image(LOGO_PATH, use_column_width=True)
    header.write("""</div>""", unsafe_allow_html=True)

    ### INPUT CONTAINER ###

    with st.session_state.input_container:
        img_prompt = st.file_uploader('', type=["jpg", "jpeg", "png"])
        if img_prompt:
            img_url = encode_image_url(img_prompt)
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
            if stt:
                prompt = stt
    input_container = st.session_state.input_container
    input_container.write("""<div class='fixed-header'>""",
                          unsafe_allow_html=True)

    #checked = st.checkbox("Check my location")
    #checked = st.button("Clinics")
    if st.session_state.show_modal:
        modal = Modal(key="clinics", title="Find nearby clinics")
        with modal.container():
            if st.button("Close"):
                st.session_state.show_modal = False
                st.experimental_rerun()  
            loc = get_geolocation()
            if loc:
                lat = loc['coords']['latitude']
                lon = loc['coords']['longitude']
                st.write(f"Your coordinates are Latitude: {lat}, Longitude: {lon}")

                nearest_clinics = get_nearest_clinics(lat, lon)
                if nearest_clinics:
                    st.success('Top 5 Nearest Clinics/Hospitals:')
                    for index, clinic in enumerate(nearest_clinics, start=1):
                        st.write(f"**Clinic/Hospital {index}:**")
                        st.write(f"Name: {clinic['Name']}")
                        st.write(f"Address: {clinic['Address']}")
                        st.write(f"Distance: {clinic['Distance']:.2f} km")
                        st.write("Status: Open Now")
                        if clinic['Photos']:
                            st.write("Images:")
                            for photo_url in clinic['Photos']:
                                st.image(photo_url)

                    m = folium.Map(location=[lat, lon], zoom_start=12)

                    # Add current location marker
                    folium.Marker(
                        [lat, lon], 
                        tooltip="You are here", 
                        icon=folium.Icon(color='blue')
                    ).add_to(m)

                    # Add markers for clinics
                    for clinic in nearest_clinics:
                        # Tooltip with image (if available)
                        tooltip_content = f"""<strong>{clinic['Name']}</strong><br>
                          {clinic['Address']}<br>
                          Distance: {clinic['Distance']:.2f} km<br>
                          Status: Open Now"""
                        if clinic['Photos']:
                            tooltip_content += f"<br><br><img src='{clinic['Photos'][0]}' width='200'>"

                        # Popup with business hours and one image (if available)
                        popup_content = f"<strong>{clinic['Name']}</strong><br>{clinic['Address']}<br>Distance: {clinic['Distance']:.2f} km<br>Status: Open Now"

                        if clinic['Photos']:
                            popup_content += f"<br><br><img src='{clinic['Photos'][0]}' width='200'>"

                        folium.Marker(
                            location=[clinic['Coordinates'][1], clinic['Coordinates'][0]], 
                            tooltip=folium.Tooltip(tooltip_content, sticky=True),
                            popup=popup_content,
                            icon=folium.Icon(color='red')
                        ).add_to(m)

                    folium_static(m)
                else:
                    st.error('No clinics found near the given location.')
            else:
                st.warning('Please enable location access.')
        

    ### CHAT CONTAINER ###
    with st.session_state.chat_container:
        for message in st.session_state.current_session:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt or img_prompt:
            if prompt:
                st.session_state.current_session.append({
                    "role": "user",
                    "content": prompt
                })
            elif img_prompt:
                st.session_state.current_session.append(
                    {"role": "user", "content": [{
                        "type": "image_url",
                        "image_url": {
                            "url": img_url
                            }
                        }]})

            with st.chat_message("user"):
                if prompt:
                    st.markdown(prompt)
                if img_prompt:
                    st.image(img_prompt, use_column_width='auto')
            with st.spinner('Processing...'), st.chat_message("assistant"):
                stream = CLIENT.chat.completions.create(
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
    hide_streamlit_style = """
                <style>
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


if __name__ == "__main__":
    initialize_session()
    main()
