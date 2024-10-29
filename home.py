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
        st.session_state.userid = "anonymous_" + str(random.randint(10000, 99999))

st.sidebar.info("userid: " + st.session_state.userid)

# Initialize responses DataFrame if not already in session
if "responses_df" not in st.session_state:
    st.session_state.responses_df = pd.DataFrame(columns=['userid', 'item', 'file', 'chosen', 'timestamp', 'attention_check'])

# Initial state to track if consent has bgiven
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False

# Consent button
if not st.session_state.consent_given:
    st.title("📷 PictoPercept")
    st.write("&nbsp;")

    col1_land, col2_land = st.columns([1, 1.618])

    with col1_land:
        with st.container(border=True):
            st.image("./data/fairface/nomargin/changeface.gif")
    with col2_land:
        st.write("""
            Imagine you are a film-maker. We will show you two images at a time, and ask who you will cast as the lead character in your next film. You must choose one person, and their picture is the only information you have. Your responses are anonymous, and the survey lasts 1 minute.

            Trust your instincts!
            """)
    
    st.write("&nbsp;")
    if st.button("Let us begin!", type="primary", use_container_width=True):
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
    
    ### Randomization of progress bar and timer ###
    if "show_timer_progress" not in st.session_state:
        st.session_state.show_timer_progress = random.choice([True, False])  # Randomly choose to show timer or not

    ### Exit button ###
    time_elapsed = datetime.datetime.now() - st.session_state.start_time
    if time_elapsed.total_seconds() > 65 and len(st.session_state.responses_df) >= 2:
        
        # Write to db here
        recordlist = st.session_state.responses_df.to_dict(orient='records')

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, record in enumerate(recordlist):
            write_to_firestore(record)
            progress = (idx + 1) / len(recordlist)
            progress_bar.progress(progress)
            status_text.text(f"Saving your responses: {int(progress * 100)}%")
        
        # Completion message
        status_text.text("All done!")
        st.write("&nbsp;")
        with st.expander("Wish to view your data?"):
            st.info("This is _not_ shown during a real survey.")
            
            file_paths = ["./data/fairface/label_train.csv", "./data/fairface/label_val.csv"]
            df2 = pd.concat((pd.read_csv(file) for file in file_paths), ignore_index=True)
            df2 = pd.merge(st.session_state.responses_df, df2, on='file', how='inner')
            st.dataframe(df2)
                
    else:
        st.write("&nbsp;")

        # Determine if we are at an attention check
        current_index = st.session_state.index
        if current_index == 4:  # Attention check at iteration 3 (remember 0-based indexing)
            image1 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[0]["file"]
            image2 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[1]["file"]
            is_attention_check = True
        elif current_index == 18:  # Attention check at iteration 10 (swapped images)
            image1 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[1]["file"]
            image2 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[0]["file"]
            is_attention_check = True
        elif current_index == 40:  # Attention check at iteration 21 (original order images)
            image1 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[0]["file"]
            image2 = "data/fairface/nomargin/" + st.session_state.attention_check_pair.iloc[1]["file"]
            is_attention_check = True
        else:  # Normal rounds
            image1 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index]["file"]
            image2 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index + 1]["file"]
            is_attention_check = False

        st.write("Who of these would you cast as the lead charater in your next film?")
        
        def save_response(selected):
            current_time = datetime.datetime.now()
            st.session_state.responses_df = pd.concat([
                st.session_state.responses_df,
                pd.DataFrame([
                    {
                        'userid': st.session_state.userid,
                        'item': (current_index // 2) + 1,
                        'file': image1.replace("data/fairface/nomargin/", ""),
                        'chosen': selected == 1,
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'show_timer_progress': st.session_state.show_timer_progress,  # Save the randomized decision
                        'attention_check': is_attention_check  # Track if this was an attention check
                    },
                    {
                        'userid': st.session_state.userid,
                        'item': (current_index // 2) + 1,
                        'file': image2.replace("data/fairface/nomargin/", ""),
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
                    "Person 1", type="primary", key="btn1", on_click=save_response, args=[1], use_container_width=True
                )
            with col2:
                button2 = st.button(
                    "Person 2", type="primary", key="btn2", on_click=save_response, args=[2], use_container_width=True
                )
            
            col1.image(image1, use_column_width="always")
            col2.image(image2, use_column_width="always")

        st.write("&nbsp;")
        
        # Only show the timer and progress bar to 50% of users
        if st.session_state.show_timer_progress:
            progress_bar = st.progress(0, text = "⏰ Try to answer as fast as possible.")

            # Loop from 1 to 5 seconds to update the progress bar
            for i in range(1, 6):
                # Update the progress bar incrementally (each step is 20% progress)
                if i == 1:
                    time.sleep(1)
                    progress_text = "⏰ Try to answer as fast as possible. Time taken: 1 second"
                elif i == 5:
                    progress_text = ":red[⏰ Try to answer as fast as possible. Time taken: More than 5 seconds!]"
                else:
                    progress_text = "⏰ Try to answer as fast as possible. Time taken: " + str(i) + " seconds"
                progress_bar.progress(i * 20, text=progress_text)  # i goes from 1 to 5, converting to percentage (20, 40, ..., 100)
                time.sleep(1)