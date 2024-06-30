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
    if "current_assistant_id" not in st.session_state:
        st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"
    if "welcome_message_displayed" not in st.session_state:
        st.session_state.welcome_message_displayed = False

initialize_session_state()

# Custom color scheme
PRIMARY_COLOR = "#d85ea7"
SECONDARY_COLOR = "#6ad85e"
BACKGROUND_COLOR = "#388bf8"
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
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 12px;
        font-size: 20px;
        background-color: #0a0b0b;
        max-width: 1400px;
        word-wrap: break-word;
        white-space: pre-wrap;
        word-break: break-word;
    }}
    .user-message {{
        background-color: #333538;
        max-width: 1400px;
    }}
    .assistant-message {{
        background-color: #093d13;
        max-width: 1400px;
    }}
    .scrollable-container {{
        max-height: 600px;
        overflow-y: auto;
    }}
    /* Custom styling for chat input */
    .stTextInput input {{
        color: white; /* Change text color */
        max-width: 1400px;
        background-color: #333538; /* Change background color */
        border-radius: 20px; /* Rounded corners */
        padding: 10px; /* Add padding */
        font-size: 24px; /* Adjust font size */
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

def rate_readiness():
    st.session_state.current_assistant_id = "asst_u4tbCd0KubyMYfKeD59bBxjM"
    save_chat()  # Save chat to create the log file
    assistant_response = run_assistant()
    if assistant_response:
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
    st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"  # Reset to main assistant
    st.experimental_rerun()

def summarize_conversation():
    st.session_state.current_assistant_id = "asst_2IN1dkowoziRpYyzSdgJbPZY"
    save_chat()  # Save chat to create the log file
    assistant_response = run_assistant()
    if assistant_response:
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
    st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"  # Reset to main assistant
    st.experimental_rerun()

def continue_conversation():
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

    # Create a container for chat and controls
    chat_container = st.container()
    controls_container = st.container()

    with chat_container:
        st.subheader("Chat")

        # Display a random welcome message if chat history is empty
        if not st.session_state.get('welcome_message_displayed', False):
            welcome_message = random.choice(welcome_messages)
            st.session_state.setdefault("chat_history", []).append({"role": "assistant", "content": welcome_message})
            st.session_state["welcome_message_displayed"] = True

        for i, message in enumerate(st.session_state["chat_history"]):
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

        user_input = st.chat_input("Type your message...", key="user_input")

        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            add_message_to_thread(user_input)

            with st.spinner("Thinking..."):
                assistant_response = run_assistant()

            if assistant_response:
                st.session_state["chat_history"].append({"role": "assistant", "content": assistant_response})

            st.experimental_rerun()

    with controls_container:
        st.markdown("<h3 style='font-size: 18px;'>Metrics</h3>", unsafe_allow_html=True)

        if st.session_state.get("chat_history"):
            sentiment = analyze_sentiment(" ".join(msg["content"] for msg in st.session_state["chat_history"]))
            st.markdown(f'<div class="sentiment-box">Sentiment: {sentiment:.2f}</div>', unsafe_allow_html=True)

        # Buttons row
        st.markdown("""
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <button onclick="startOver()" style="background-color: #a1a53b; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">Start Over</button>
            <button onclick="saveChat()" style="background-color: #3f3ba5; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">Save Chat</button>
            <button onclick="summarize()" style="background-color: #a53b6c; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">Summarize</button>
            <button onclick="rateReadiness()" style="background-color: #a53b3b; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">Review Readiness</button>
        </div>
        """, unsafe_allow_html=True)

    # Add custom JavaScript to trigger Streamlit actions
    st.markdown("""
    <script>
    function startOver() {
        document.querySelector('button[k="start_over"]').click();
    }
    function saveChat() {
        document.querySelector('button[k="save_chat"]').click();
    }
    function summarize() {
        document.querySelector('button[k="summarize"]').click();
    }
    function rateReadiness() {
        document.querySelector('button[k="rate_readiness"]').click();
    }
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
