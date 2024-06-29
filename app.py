import streamlit as st
import openai
from openai import OpenAI
import time
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import random

# Initialize NLTK
nltk.download('vader_lexicon', quiet=True)

# Streamlit configuration
st.set_page_config(page_title="Motivational Interviewing Chatbot", layout="wide")

# Custom color scheme
PRIMARY_COLOR = "#4CAF50"  # Green
SECONDARY_COLOR = "#2196F3"  # Blue
BACKGROUND_COLOR = "#F1F8E9"  # Light green

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
    .stTextInput>div>div>input {{
        border-radius: 20px;
    }}
    .sentiment-box {{
        padding: 10px;
        border-radius: 5px;
        background-color: {SECONDARY_COLOR};
        color: white;
        display: inline-block;
    }}
    .avatar {{
        width: 50px;
        height: 50px;
        margin-right: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

# 8-bit pixel avatar
AVATAR_HTML = """
<svg class="avatar" viewBox="0 0 100 100">
    <rect x="0" y="0" width="100" height="100" fill="#FFD700"/>
    <rect x="30" y="30" width="15" height="15" fill="#000000"/>
    <rect x="55" y="30" width="15" height="15" fill="#000000"/>
    <rect x="40" y="60" width="20" height="10" fill="#FF0000"/>
</svg>
"""

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "confidence" not in st.session_state:
    st.session_state.confidence = 5
if "importance" not in st.session_state:
    st.session_state.importance = 5
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Pre-configured Assistant ID
ASSISTANT_ID = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"

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
        assistant_id=ASSISTANT_ID
    )
    
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
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
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = [Paragraph(f"{msg['role'].capitalize()}: {msg['content']}", styles['Normal']) for msg in st.session_state.chat_history]
    doc.build(flowables)
    return buffer.getvalue()

def display_chat_history():
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"], avatar=AVATAR_HTML if message["role"] == "assistant" else None):
            st.write(message["content"])

def get_initial_question():
    return random.choice([
        "So, what's next for you?",
        "So, where do you go from here?",
        "So, what do you think you will do?",
        "So, what are you going to do?"
    ])

def main():
    st.title("Motivational Interviewing Chatbot")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Metrics")
        
        if st.session_state.chat_history:
            sentiment = analyze_sentiment(" ".join(msg["content"] for msg in st.session_state.chat_history))
            st.markdown(f'<div class="sentiment-box">Overall Sentiment: {sentiment:.2f}</div>', unsafe_allow_html=True)
        
        st.write("How confident are you in your ability to make this change?")
        st.session_state.confidence = st.slider("Confidence", 0, 10, st.session_state.confidence)
        
        st.write("How important is this change to you?")
        st.session_state.importance = st.slider("Importance", 0, 10, st.session_state.importance)
        
        if st.button("Export Conversation to PDF"):
            pdf = export_to_pdf()
            st.download_button(
                label="Download PDF",
                data=pdf,
                file_name="conversation_summary.pdf",
                mime="application/pdf"
            )

    with col2:
        st.subheader("Chat")
        chat_container = st.container()

        with chat_container:
            display_chat_history()

            if not st.session_state.conversation_started:
                initial_message = f"I'm here to help you make a change. {get_initial_question()}"
                st.session_state.chat_history.append({"role": "assistant", "content": initial_message})
                add_message_to_thread(initial_message)
                st.session_state.conversation_started = True
                st.experimental_rerun()

            user_input = st.chat_input("Type your message here...")

            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                add_message_to_thread(user_input)
                assistant_response = run_assistant()
                if assistant_response:
                    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                    st.experimental_rerun()
                else:
                    st.error("Failed to get a response from the assistant. Please try again.")

if __name__ == "__main__":
    main()
