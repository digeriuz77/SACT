import streamlit as st
import openai
from openai import OpenAI
import time
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from io import BytesIO
import re
import random

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
        font-size: 14px;
        margin-bottom: 10px;
    }}
    .chat-message {{
        padding: 10px;
        border-radius: 5px;
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

def export_to_pdf():
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    flowables = [Paragraph(f"{msg['role'].capitalize()}: {msg['content']}", styles['Normal']) for msg in st.session_state.chat_history]
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(flowables)
    return buffer.getvalue()

def check_for_importance_slider(text):
    return "On a scale from 0 to 10, how important" in text

def check_for_confidence_slider(text):
    return "on a scale from 0 to 10, how confident" in text

def check_for_summary_condition(text):
    return "Would you like a summary of our conversation?" in text

def check_for_readiness_review(text):
    return "review your readiness to change" in text

def check_for_exit_condition(text):
    return "exit the chat" in text

def on_slider_change(slider_type):
    if slider_type == "importance":
        value = st.session_state.importance
        message = f"The importance of this change to me is {value} out of 10."
    else:  # confidence
        value = st.session_state.confidence
        message = f"My confidence in my ability to change is {value} out of 10."
    
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

def display_sliders():
    if st.session_state.show_importance_slider:
        importance = st.slider("Importance of change:", 0, 10, st.session_state.importance, key="importance_slider")
        if importance != st.session_state.importance:
            st.session_state.importance = importance
            st.session_state.importance_value_provided = True
            st.session_state.show_importance_slider = False
            on_slider_change("importance")
            st.experimental_rerun()

    if st.session_state.show_confidence_slider:
        confidence = st.slider("Confidence in ability to change:", 0, 10, st.session_state.confidence, key="confidence_slider")
        if confidence != st.session_state.confidence:
            st.session_state.confidence = confidence
            st.session_state.confidence_value_provided = True
            st.session_state.show_confidence_slider = False
            on_slider_change("confidence")
            st.experimental_rerun()

welcome_messages = [
    "Hi, I'm a coachbot that helps you make changes. What change is next for you?",
    "Welcome, I'm a coachbot that helps you make changes. What change would you like to make?",
    "Hi there! I'm a coachbot that aids in decision making. What are you planning to change?"
]

def main():
    st.title("Motivational Interviewing Chatbot")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("<h3 style='font-size: 18px;'>Metrics</h3>", unsafe_allow_html=True)
        
        if st.session_state.chat_history:
            sentiment = analyze_sentiment(" ".join(msg["content"] for msg in st.session_state.chat_history))
            st.markdown(f'<div class="sentiment-box">Sentiment: {sentiment:.2f}</div>', unsafe_allow_html=True)
        
        if st.session_state.show_readiness_button:
            st.button("Rate my readiness to change", on_click=rate_readiness, key="rate_readiness", type="primary")

    with col2:
        st.subheader("Chat")
        
        # Display a random welcome message if chat history is empty
        if not st.session_state.welcome_message_displayed:
            welcome_message = random.choice(welcome_messages)
            st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
            st.session_state.welcome_message_displayed = True
        
        for i, message in enumerate(st.session_state.chat_history):
            st.markdown(f"""
                <div class="chat-message {'user-message' if message['role'] == 'user' else 'assistant-message'}">
                    <b>{message['role'].capitalize()}:</b> {message['content']}
                </div>
            """, unsafe_allow_html=True)
            
            if message['role'] == 'assistant':
                if check_for_importance_slider(message['content']) and not st.session_state.importance_value_provided:
                    st.session_state.show_importance_slider = True
                elif check_for_confidence_slider(message['content']) and not st.session_state.confidence_value_provided:
                    st.session_state.show_confidence_slider = True
                elif check_for_summary_condition(message['content']):
                    st.session_state.show_summary_options = True
                elif check_for_readiness_review(message['content']):
                    st.session_state.show_readiness_button = True
                elif check_for_exit_condition(message['content']):
                    pdf = export_to_pdf()
                    st.download_button(
                        label="Export Chat to PDF",
                        data=pdf,
                        file_name="conversation_summary.pdf",
                        mime="application/pdf"
                    )

        # Call the function to display sliders
        display_sliders()

        if st.session_state.show_summary_options:
            col1, col2 = st.columns(2)
            with col1:
                st.button("Please summarize", on_click=summarize_conversation)
            with col2:
                st.button("No, continue", on_click=continue_conversation)

        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            add_message_to_thread(user_input)
            
            with st.spinner("Thinking..."):
                assistant_response = run_assistant()
            
            if assistant_response:
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                st.session_state.show_summary_options = check_for_summary_condition(assistant_response)
                st.session_state.show_readiness_button = check_for_readiness_review(assistant_response)
            
            st.experimental_rerun()

if __name__ == "__main__":
    main()
