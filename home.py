import streamlit as st
import pandas as pd
import time
import datetime
import random
from google.cloud import firestore
from google.oauth2 import service_account
import json

# Set up the Streamlit page configuration and hide menu, footer, header
st.set_page_config(page_icon="📷", page_title="PictoPercept", layout="centered", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}list_of
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

occupations = [
            "dokter",
            "astronaut",
            "financieel directeur",
            "wetenschapper",
            "politieagent",
            "bouwvakker",
            "elektromonteur",
            "verpleegkundige",
            "kapper",
            "leerkracht"
        ]

# authenticate to Firestore with own credentials
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="picsurvey1")

# Firestore collection reference
responses_collection = db.collection('responses')

def write_to_firestore(record):
    """ Function to write a record to Firestore """
    doc_ref = responses_collection.document()  # Create a new document in Firestore
    doc_ref.set(record)  # Set the document with the data from the record

# Initialize user ID and DataFrame if not already in session
if "userid" not in st.session_state:
    if "choice_respondent" in st.query_params:
        st.session_state.userid = str(st.query_params.choice_respondent)
    else:
        st.session_state.userid = "unresolved_" + str(random.randint(10000, 99999))

st.sidebar.info("userid: " + st.session_state.userid)

# Initialize responses DataFrame if not already in session
if "responses_df" not in st.session_state:
    st.session_state.responses_df = pd.DataFrame(columns=['userid', 'item', 'file', 'job', 'chosen', 'timestamp', 'attention_check'])

# Initial state to track if consent has bgiven
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False

# Consent button
if not st.session_state.consent_given:
    st.title("📷 PictoPercept")
    st.write("&nbsp;")
    st.write("""
            Welkom bij PictoPercept! Je ziet paren foto's en functietitel, zoals "Wie van deze is leraar?" of "Wie van deze is kapper?" Kies de persoon die volgens jou het beste bij de functie past door op de knop te klikken.

            Vertrouw op je instinct!
            """)
    st.write("&nbsp;")
    if st.button("Laten we beginnen!", type="primary", use_container_width=True):
        st.session_state.consent_given = True
        st.rerun()

if st.session_state.consent_given:
    
    if "data" not in st.session_state:
        # for first run
        file_paths = ["./data/fairface/label_train.csv", "./data/fairface/label_val.csv"]
        df = pd.concat((pd.read_csv(file) for file in file_paths), ignore_index=True)
        df = df[~df['age'].isin(['0-2', '3-9', '10-19'])]  # drop non-adults
        df = df.sample(frac=1).reset_index(drop=True)  # shuffle rows
        st.session_state.data = df[["file"]]
        st.session_state.index = 0
        st.session_state.start_time = datetime.datetime.now()
        # Select the last pair of images for the attention check
        st.session_state.attention_check_pair = st.session_state.data.iloc[-2:]
        # Randomly choose a job title for the attention check
        st.session_state.attention_check_job = random.choice(occupations)

    ### Randomization of progress bar and timer ###
    if "show_timer_progress" not in st.session_state:
        st.session_state.show_timer_progress = random.choice([True, False])  # Randomly choose to show timer or not

    ### Exit button ###
    time_elapsed = datetime.datetime.now() - st.session_state.start_time
    if time_elapsed.total_seconds() > 65 and len(st.session_state.responses_df) >= 2:

        # write to db here
        with st.spinner('Saving your responses...'):
            recordlist = st.session_state.responses_df.to_dict(orient='records')
            for record in recordlist:
                write_to_firestore(record)

        redirect_link = f"https://surveys.thechoice.nl/s3/UVA2305-PictoPercept-Complete?choice_respondent={st.session_state.userid}"
        st.markdown(f'<span style="font-size:20px;"><a href="{redirect_link}" target="_self">Click here to exit this tool!</a></span>', unsafe_allow_html=True)
        
    else:
        st.write("&nbsp;")

        # Determine if we are at an attention check
        current_index = st.session_state.index
        if current_index == 4:  # Attention check at iteration 3 (remember 0-based indexing)
            image1 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[0]["file"]
            image2 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[1]["file"]
            job = st.session_state.attention_check_job  # Use the same job for both attention checks
            is_attention_check = True
        elif current_index == 18:  # Attention check at iteration 10 (swapped images)
            image1 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[1]["file"]
            image2 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[0]["file"]
            job = st.session_state.attention_check_job  # Use the same job for both attention checks
            is_attention_check = True
        else:  # Normal rounds
            image1 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index]["file"]
            image2 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index + 1]["file"]
            job = random.choice(occupations)
            is_attention_check = False

        TEXT = "<span style='font-size:20px;'>Wie van deze personen is een **" + job.upper() + "**?</span>"
        st.write(TEXT, unsafe_allow_html=True)
        
        def save_response(selected):
            current_time = datetime.datetime.now()
            st.session_state.responses_df = pd.concat([
                st.session_state.responses_df,
                pd.DataFrame([
                    {
                        'userid': st.session_state.userid,
                        'item': (current_index // 2) + 1,
                        'file': image1.replace("data/fairface/nomargin/", ""),
                        'job': job,
                        'chosen': selected == 1,
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'show_timer_progress': st.session_state.show_timer_progress,  # Save the randomized decision
                        'attention_check': is_attention_check  # Track if this was an attention check
                    },
                    {
                        'userid': st.session_state.userid,
                        'item': (current_index // 2) + 1,
                        'file': image2.replace("data/fairface/nomargin/", ""),
                        'job': job,
                        'chosen': selected == 2,
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'show_timer_progress': st.session_state.show_timer_progress,
                        'attention_check': is_attention_check  # Track if this was an attention check
                    }
                ])
            ], ignore_index=True)
            # Next run now!
            st.session_state.index += 2

        ### Main Buttons Display ###

        with st.container(border=True):
            col1, col2 = st.columns(2, gap="large")
            with col1:
                button1 = st.button(
                    "Persoon 1", type="primary", key="btn1", on_click=save_response, args=[1], use_container_width=True
                )
            with col2:
                button2 = st.button(
                    "Persoon 2", type="primary", key="btn2", on_click=save_response, args=[2], use_container_width=True
                )
            
            col1.image(image1, use_column_width="always")
            col2.image(image2, use_column_width="always")

        st.write("&nbsp;")
        
        # Only show the timer and progress bar to 50% of users
        if st.session_state.show_timer_progress:
            progress_bar = st.progress(0, text = "⏰ Probeer zo snel mogelijk te antwoorden.")

            # Loop from 1 to 5 seconds to update the progress bar
            for i in range(1, 6):
                # Update the progress bar incrementally (each step is 20% progress)
                if i == 1:
                    time.sleep(1)
                    progress_text = "⏰ Probeer zo snel mogelijk te antwoorden. Tijdsduur: 1 seconde"
                elif i == 5:
                    progress_text = ":red[⏰ Probeer zo snel mogelijk te antwoorden. Tijdsduur: Meer dan 5 seconden!]"
                else:
                    progress_text = "⏰ Probeer zo snel mogelijk te antwoorden. Tijdsduur: " + str(i) + " seconden"
                progress_bar.progress(i * 20, text=progress_text)  # i goes from 1 to 5, converting to percentage (20, 40, ..., 100)
                time.sleep(1)