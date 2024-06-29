import streamlit as st
import openai
from openai import OpenAI
from openai import AssistantEventHandler
from typing_extensions import override
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
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Assistant ID (replace with your actual Assistant ID)
ASSISTANT_ID = "asst_your_assistant_id_here"

class ChatEventHandler(AssistantEventHandler):
    def __init__(self):
        self.full_response = ""
    
    @override
    def on_text_created(self, text) -> None:
        pass
    
    @override
    def on_text_delta(self, delta, snapshot):
        self.full_response += delta.value
        st.session_state.chat_history[-1]["content"] = self.full_response
        st.experimental_rerun()

def create_thread_if_not_exists():
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

def add_message_to_thread(role, content):
    create_thread_if_not_exists()
    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role=role,
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
    
    st.session_state.chat_history.append({"role": "assistant", "content": ""})
    
    with st.spinner("Thinking..."):
        event_handler = ChatEventHandler()
        with client.beta.threads.runs.stream(
            thread_id=st.session_state.thread_id,
            run_id=run.id,
            event_handler=event_handler,
        ) as stream:
            stream.until_done()

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

def main():
    st.title("Motivational Interviewing Chatbot")

    # User input
    user_input = st.text_input("You:", key="user_input")

    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Add message to thread and run assistant
        add_message_to_thread("user", user_input)
        run_assistant()

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Export chat to PDF
    if st.button("Export Conversation to PDF"):
        pdf = export_to_pdf()
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name="conversation_summary.pdf",
            mime="application/pdf"
        )

    # Display sentiment analysis
    if st.session_state.chat_history:
        all_text = " ".join([msg["content"] for msg in st.session_state.chat_history])
        sentiment = analyze_sentiment(all_text)
        st.sidebar.markdown(f"**Overall Sentiment:** {sentiment:.2f}")

if __name__ == "__main__":
    main()
