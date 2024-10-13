import streamlit as st
import pandas as pd
import time
import datetime
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
    if "choice_respondent" in st.query_params:
        st.session_state.userid = str(st.query_params.choice_respondent)
    else:
        st.session_state.userid = "unresolved_" + str(random.randint(10000, 99999))

st.sidebar.info("userid: " + st.session_state.userid)

# Initialize responses DataFrame if not already in session
if "responses_df" not in st.session_state:
    st.session_state.responses_df = pd.DataFrame(columns=['userid', 'item', 'file', 'job', 'chosen', 'timestamp'])

# Initial state to track if consent has been given
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False

# Consent button
if not st.session_state.consent_given:
    st.title("📷 PictoPercept")
    st.write("&nbsp;")
    st.write("""
            Welkom bij PictoPercept! Je ziet paren foto's en een functietitel, zoals "Wie van deze is een leraar?" of "Wie van deze is een kapper?" Kies de persoon die volgens jou het beste bij de functie past door op de knop te klikken.

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
        df = df[~df['age'].isin(['0-2', '3-9', '10-19'])]
        df = df.sample(frac=1).reset_index(drop=True)
        st.session_state.data = df[["file"]]
        st.session_state.index = 0
        st.session_state.start_time = datetime.datetime.now()

    ### Randomization of progress bar and timer ###
    if "show_timer_progress" not in st.session_state:
        st.session_state.show_timer_progress = random.choice([True, False])  # Randomly choose to show or not

    ### Exit button ###
    time_elapsed = datetime.datetime.now() - st.session_state.start_time
    if time_elapsed.total_seconds() > 65 and len(st.session_state.responses_df) >= 2:
        # write to db here
        redirect_link = f"https://surveys.thechoice.nl/s3/UVA2305-PictoPercept-Complete?choice_respondent={st.session_state.userid}"
        st.markdown(f'<span style="font-size:20px;"><a href="{redirect_link}" target="_self">Click here to exit this tool!</a></span>', unsafe_allow_html=True)
        
    else:
        st.write("&nbsp;")
        
        # Lijst van niet-geslachtsgebonden beroepen
        occupations = [
            "een dokter",
            "een astronaut",
            "een financieel directeur",
            "een wetenschapper",
            "een politieagent",
            "een bouwvakker",
            "een elektromonteur",
            "een verpleegkundige",
            "een kapper",
            "een leerkracht"
        ]
        job = str(random.choice(occupations))
        TEXT = "<span style='font-size:24px;'>Wie van deze personen is _**" + job + "**_?</span>"


        st.write(TEXT, unsafe_allow_html=True)

        ### Choosing images ###

        current_index = st.session_state.index
        image1 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index]["file"]
        image2 = "data/fairface/nomargin/" + st.session_state.data.iloc[current_index + 1]["file"]
        
        def save_response(selected):
            current_time = datetime.datetime.now()
            st.session_state.responses_df = pd.concat([
                st.session_state.responses_df,
                pd.DataFrame([
                    {'userid': st.session_state.userid, 'item': (current_index // 2) + 1, 'file': image1.replace("data/fairface/nomargin/", ""), 'job': job, 'chosen': selected == 1, 'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S")},
                    {'userid': st.session_state.userid, 'item': (current_index // 2) + 1, 'file': image2.replace("data/fairface/nomargin/", ""), 'job': job, 'chosen': selected == 2, 'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S")}
                ])
            ], ignore_index=True)
            # next run now!
            st.session_state.index += 2
        
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
                        'show_timer_progress': st.session_state.show_timer_progress  # Save the randomized decision
                    },
                    {
                        'userid': st.session_state.userid,
                        'item': (current_index // 2) + 1,
                        'file': image2.replace("data/fairface/nomargin/", ""),
                        'job': job,
                        'chosen': selected == 2,
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'show_timer_progress': st.session_state.show_timer_progress  # Save the randomized decision
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

    # st.dataframe(st.session_state.responses_df)