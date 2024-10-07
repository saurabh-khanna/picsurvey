import streamlit as st
import pandas as pd
import uuid
import time
import random

# Set up the Streamlit page configuration and hide menu, footer, header
st.set_page_config(page_icon="📷", page_title="PictoPercept", layout="centered", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize user ID and DataFrame if not already in session
if "userid" not in st.session_state:
    st.session_state.userid = str(uuid.uuid4())

# Initial state to track if consent has been given
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False

# Consent button
if not st.session_state.consent_given:
    st.title("📷 PictoPercept")
    st.write("&nbsp;")
    if st.button("Let us begin!", type="primary", use_container_width=True):
        st.session_state.consent_given = True
        st.rerun()

if st.session_state.consent_given:
    # List of non-gendered occupations
    occupations = ['a doctor', 'a lawyer', 'a nurse', 'an author', 'a teacher', 'an engineer', 'a scientist', 'a chef', 'an artist', 'an architect', 'a pilot', 'a journalist', 'a dentist', 'a therapist', 'an accountant', 'a musician', 'a designer', 'a programmer', 'a pharmacist', 'a plumber', 'an electrician', 'a librarian', 'an analyst', 'a consultant', 'an entrepreneur', 'a researcher', 'a technician', 'an editor', 'a translator', 'a veterinarian', 'a social worker', 'a photographer']

    TEXT = "<span style='font-size:24px;'>Who of these is _**" + str(random.choice(occupations)) + "**_?</span>"

    st.write(TEXT, unsafe_allow_html=True)

    if "data" not in st.session_state:
        # for first run
        file_paths = ["./data/fairface/label_train.csv", "./data/fairface/label_val.csv"]
        df = pd.concat((pd.read_csv(file) for file in file_paths), ignore_index=True)
        df = df[~df['age'].isin(['0-2', '3-9', '10-19'])]
        df = df.sample(frac=1).reset_index(drop=True)
        st.session_state.data = df
        st.session_state.index = 0

    # Main button click handling logic
    def next_run():
        st.session_state.index += 2

    ### Choosing images ###

    current_index = st.session_state.index
    image1 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index]["file"]
    image2 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index + 1]["file"]

    ### Main Buttons Display ###

    with st.container(border=True):
        col1, col2 = st.columns(2, gap="large")
        with col1:
            button1 = st.button(
                "Person 1", type="primary", key="btn1", on_click=next_run, use_container_width=True
            )
        with col2:
            button2 = st.button(
                "Person 2", type="primary", key="btn2", on_click=next_run, use_container_width=True
            )
        
        col1.image(image1, use_column_width="always")
        col2.image(image2, use_column_width="always")

    st.write("&nbsp;")
    st.write("🕰️ Try to answer in less than 5 seconds...")
    progress_bar = st.progress(0)

    # Loop from 1 to 5 seconds to update the progress bar
    for i in range(1, 6):
        # Update the progress bar incrementally (each step is 20% progress)
        if i == 1:
            time.sleep(1)
            progress_text = ":green[Time taken: " + str(i) + " second]"
        elif i == 5:
            progress_text = ":red[Time taken: More than " + str(i) + " seconds!!!]"
        else:
            progress_text = ":green[Time taken: " + str(i) + " seconds]"
        progress_bar.progress(i * 20, text=progress_text)  # i goes from 1 to 5, converting to percentage (20, 40, ..., 100)
        time.sleep(1)