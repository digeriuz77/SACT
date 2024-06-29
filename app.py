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
import os

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
    }}
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "introduction"
if "confidence" not in st.session_state:
    st.session_state.confidence = 5
if "importance" not in st.session_state:
    st.session_state.importance = 5

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Updated Assistant ID
ASSISTANT_ID = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"

def create_thread_if_not_exists():
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

def add_message_to_thread(content):
    create_thread_if_not_exists()
    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=content
    )
    return message

def run_assistant(instructions=None):
    create_thread_if_not_exists()
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID,
        instructions=instructions
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
    
    assistant_message = messages.data[0].content[0].text.value
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})
    return assistant_message

def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)['compound']

def export_to_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = []

    for message in st.session_state.chat_history:
        flowables.append(Paragraph(f"{message['role'].capitalize()}: {message['content']}", styles['Normal']))
        flowables.append(Paragraph("<br/><br/>", styles['Normal']))

    doc.build(flowables)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def display_chat_history():
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

def main():
    st.title("Motivational Interviewing Chatbot")

    # Sentiment analysis in a small box at the top left
    if st.session_state.chat_history:
        all_text = " ".join([msg["content"] for msg in st.session_state.chat_history])
        sentiment = analyze_sentiment(all_text)
        st.markdown(f"""
            <div class="sentiment-box">
                Overall Sentiment: {sentiment:.2f}
            </div>
        """, unsafe_allow_html=True)

    # Main chat area
    chat_container = st.container()

    # Contextual GUI elements
    gui_container = st.container()

    with chat_container:
        display_chat_history()

        # User input
        user_input = st.chat_input("Type your message here...")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            add_message_to_thread(user_input)
            assistant_response = run_assistant()
            st.experimental_rerun()

    with gui_container:
        if st.session_state.current_stage == "confidence_ruler":
            st.write("How confident are you in your ability to make this change?")
            st.session_state.confidence = st.slider("Confidence", 0, 10, 5)
            if st.button("Continue"):
                st.session_state.current_stage = "importance_ruler"
                st.experimental_rerun()

        elif st.session_state.current_stage == "importance_ruler":
            st.write("How important is this change to you?")
            st.session_state.importance = st.slider("Importance", 0, 10, 5)
            if st.button("Continue"):
                st.session_state.current_stage = "main_conversation"
                st.experimental_rerun()

        elif st.session_state.current_stage == "main_conversation":
            if st.button("Export Conversation to PDF"):
                pdf = export_to_pdf()
                st.download_button(
                    label="Download PDF",
                    data=pdf,
                    file_name="conversation_summary.pdf",
                    mime="application/pdf"
                )

    # Logic to change stages based on conversation
    if len(st.session_state.chat_history) == 2:  # After first exchange
        st.session_state.current_stage = "confidence_ruler"
    elif len(st.session_state.chat_history) == 4:  # After second exchange
        st.session_state.current_stage = "importance_ruler"
    elif len(st.session_state.chat_history) > 4:
        st.session_state.current_stage = "main_conversation"

if __name__ == "__main__":
    main()
