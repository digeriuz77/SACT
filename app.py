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

# Assistant ID for DecisionBalanceandPlan
ASSISTANT_ID = "asst_J7TcXqBWKeZdhdiS8YigHCik"

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

def main():
    st.title("Motivational Interviewing Chatbot")

    # User input
    user_input = st.text_input("You:", key="user_input")

    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Add message to thread and run assistant
        add_message_to_thread(user_input)
        assistant_response = run_assistant()

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
