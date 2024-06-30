import streamlit as st
import openai
from openai import OpenAI
import time
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from io import BytesIO
import re
import random
import logging
import json
from datetime import datetime
import os

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Initialize NLTK
nltk.download('vader_lexicon', quiet=True)

# Streamlit configuration
st.set_page_config(page_title="Motivational Interviewing Chatbot", layout="wide")

# Initialize session state
def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "confidence" not in st.session_state:
        st.session_state.confidence = 5
    if "importance" not in st.session_state:
        st.session_state.importance = 5
    if "importance_value_provided" not in st.session_state:
        st.session_state.importance_value_provided = False
    if "confidence_value_provided" not in st.session_state:
        st.session_state.confidence_value_provided = False
    if "show_importance_slider" not in st.session_state:
        st.session_state.show_importance_slider = False
    if "show_confidence_slider" not in st.session_state:
        st.session_state.show_confidence_slider = False
    if "show_summary_options" not in st.session_state:
        st.session_state.show_summary_options = False
    if "show_readiness_button" not in st.session_state:
        st.session_state.show_readiness_button = False
    if "current_assistant_id" not in st.session_state:
        st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"
    if "welcome_message_displayed" not in st.session_state:
        st.session_state.welcome_message_displayed = False

initialize_session_state()

# Custom color scheme
PRIMARY_COLOR = "#d85ea7"
SECONDARY_COLOR = "#6ad85e"
BACKGROUND_COLOR = "#281b4a"
READINESS_BUTTON_COLOR = "#cc5ed8"

# Custom CSS
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BACKGROUND_COLOR};
    }}
    .stButton>button {{
        color: white;
        background-color: {PRIMARY_COLOR};
        border-radius: 20px;
    }}
    .readiness-button {{
        color: white;
        background-color: {READINESS_BUTTON_COLOR} !important;
        border-radius: 20px;
    }}
    .sentiment-box {{
        padding: 5px;
        border-radius: 5px;
        background-color: {SECONDARY_COLOR};
        color: white;
        font-size: 18px;
        margin-bottom: 16px;
    }}
    .chat-message {{
        padding: 10px;
        border-radius: 9px;
        margin-bottom: 10px;
        word-wrap: break-word;
        white-space: pre-wrap;
        word-break: break-word;
    }}
    .user-message {{
        background-color: #5e6ad8;
    }}
    .assistant-message {{
        background-color: #23082c;
    }}
    div.css-1oe6wy4.e1fqkh3o9 {{
        position: fixed;
        top: 0;
        left: 0;
        bottom: 0;
        width: 20%;
        padding: 20px;
        background-color: #281b4a;
        overflow-y: auto;
    }}
    </style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def create_thread_if_not_exists():
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

def add_message_to_thread(content):
    create_thread_if_not_exists()
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=content
    )

def run_assistant():
    create_thread_if_not_exists()
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=st.session_state.current_assistant_id
    )
    
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            st.error(f"Run failed: {run_status.last_error}")
            return None
        time.sleep(1)
    
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    
    return messages.data[0].content[0].text.value

def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)['compound']

def check_for_importance_slider(text):
    return "on a scale of 0-10, how important" in text.lower()

def check_for_confidence_slider(text):
    return "on a scale of 0-10, how confident" in text.lower()

def check_for_summary_condition(text):
    return "Would you like a summary of our conversation?" in text.lower()

def check_for_readiness_review(text):
    return "review your readiness to change" in text.lower()

def on_slider_change(slider_type):
    if slider_type == "importance":
        value = st.session_state.importance
        message = f"On a scale of 0-10, the importance of this change to me is {value}."
    else:  # confidence
        value = st.session_state.confidence
        message = f"On a scale of 0-10, my confidence in making this change is {value}."
    
    st.session_state.chat_history.append({"role": "user", "content": message})
    add_message_to_thread(message)
    with st.spinner("Thinking..."):
        assistant_response = run_assistant()
    if assistant_response:
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
    
    st.experimental_rerun()

def rate_readiness():
    st.session_state.current_assistant_id = "asst_u4tbCd0KubyMYfKeD59bBxjM"
    assistant_response = run_assistant()
    if assistant_response:
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
    st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"  # Reset to main assistant
    st.session_state.show_readiness_button = False  # Hide the button after use
    st.experimental_rerun()

def summarize_conversation():
    st.session_state.current_assistant_id = "asst_2IN1dkowoziRpYyzSdgJbPZY"
    assistant_response = run_assistant()
    if assistant_response:
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
    st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"  # Reset to main assistant
    st.session_state.show_summary_options = False
    st.experimental_rerun()

def continue_conversation():
    st.session_state.show_summary_options = False
    st.experimental_rerun()

def reset_chat():
    st.session_state.chat_history = []
    st.session_state.welcome_message_displayed = False
    st.experimental_rerun()

def save_chat():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"chat_history_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(st.session_state.chat_history, f)
    st.success(f"Chat history saved as {filename}")

def get_saved_chats():
    return [f for f in os.listdir(".") if f.startswith("chat_history_") and f.endswith(".json")]

def load_chat(filename):
    with open(filename, "r") as f:
        st.session_state.chat_history = json.load(f)
    st.session_state.welcome_message_displayed = True
    st.experimental_rerun()

welcome_messages = [
    "Hi there! I'm a coach specializing in motivational interviewing. What change are you considering?",
    "Hello! I'm here to guide you through the process of change. What would you like to focus on today?",
    "Welcome! As a motivational interviewing coach, I'm here to support you. What change are you thinking about making?"
]

def main():
    st.title("Motivational Interviewing Chatbot")

    # Custom CSS for slider
    st.markdown(
        """
        <style>
        /* Customize the slider container */
        div.stSlider > div[data-baseweb="slider"] > div {
            background: rgb(1 1 1 / 0%);
        }

        /* Customize the slider cursor */
        div.stSlider > div[data-baseweb="slider"] > div > div > div[role="slider"] {
            background-color: rgb(255, 0, 0); /* Red dot */
            box-shadow: rgb(255 0 0 / 20%) 0px 0px 0px 0.2rem;
        }

        /* Customize the slider numbers */
        div.stSlider > div[data-baseweb="slider"] > div > div > div > div {
            color: rgb(255, 255, 255); /* White numbers */
        }

        /* Increase the font size of the slider label */
        div.stSlider label {
            font-size: 18px;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("<h3 style='font-size: 18px;'>Metrics</h3>", unsafe_allow_html=True)

        if st.session_state.chat_history:
            sentiment = analyze_sentiment(" ".join(msg["content"] for msg in st.session_state.chat_history))
            st.markdown(f'<div class="sentiment-box">Sentiment: {sentiment:.2f}</div>', unsafe_allow_html=True)

        st.button("Start Over", on_click=reset_chat, key="start_over")
        st.button("Save Chat", on_click=save_chat, key="save_chat")
        
        saved_chats = get_saved_chats()
        selected_chat = st.selectbox("Load Chat", [""] + saved_chats, key="load_chat")
        if selected_chat:
            load_chat(selected_chat)

    with col2:
        st.subheader("Chat")

        slider_container = st.empty()

        # Display a random welcome message if chat history is empty
        if not st.session_state.welcome_message_displayed:
            welcome_message = random.choice(welcome_messages)
            st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
            st.session_state.welcome_message_displayed = True

        for i, message in enumerate(st.session_state.chat_history):
            if message['role'] == 'assistant':
                st.markdown(f"""
                    <div class="chat-message assistant-message">
                        🐙 {message['content']}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message user-message">
                        <b>You:</b> {message['content']}
                    </div>
                """, unsafe_allow_html=True)

            if message['role'] == 'assistant':
                if check_for_readiness_review(message['content']) and not st.session_state.show_readiness_button:
                    st.session_state.show_readiness_button = True
                elif check_for_summary_condition(message['content']) and not st.session_state.show_summary_options:
                    st.session_state.show_summary_options = True
                elif check_for_importance_slider(message['content']) and not st.session_state.importance_value_provided:
                    st.session_state.show_importance_slider = True
                elif check_for_confidence_slider(message['content']) and not st.session_state.confidence_value_provided:
                    st.session_state.show_confidence_slider = True

        if st.session_state.show_importance_slider:
            with slider_container:
                importance = st.slider("On a scale of 0-10, how important is this change to you?", 0, 10, st.session_state.importance, key="importance_slider")
                if importance != st.session_state.importance:
                    st.session_state.importance = importance
                    st.session_state.importance_value_provided = True
                    st.session_state.show_importance_slider = False
                    on_slider_change("importance")

        if st.session_state.show_confidence_slider:
            with slider_container:
                confidence = st.slider("On a scale of 0-10, how confident are you in making this change?", 0, 10, st.session_state.confidence, key="confidence_slider")
                if confidence != st.session_state.confidence:
                    st.session_state.confidence = confidence
                    st.session_state.confidence_value_provided = True
                    st.session_state.show_confidence_slider = False
                    on_slider_change("confidence")
                    
        if not st.session_state.show_importance_slider and not st.session_state.show_confidence_slider:
            slider_container.empty()

        if st.session_state.show_readiness_button:
            st.button("Review my readiness to change", on_click=rate_readiness, key="rate_readiness", type="primary")

        if st.session_state.show_summary_options:
            col1, col2 = st.columns(2)
            with col1:
                st.button("Summarize our conversation", on_click=summarize_conversation)
            with col2:
                st.button("Continue our conversation", on_click=continue_conversation)

        user_input = st.chat_input("Type your message...", key="user_input")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            add_message_to_thread(user_input)

            with st.spinner("Thinking..."):
                assistant_response = run_assistant()

            if assistant_response:
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

            st.experimental_rerun()

if __name__ == "__main__":
    main()
