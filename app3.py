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

# Initialize NLTK
nltk.download('vader_lexicon', quiet=True)

# Streamlit configuration
st.set_page_config(page_title="Motivational Interviewing Chatbot", layout="wide")

# Custom color scheme
PRIMARY_COLOR = "#4CAF50"
SECONDARY_COLOR = "#2196F3"
BACKGROUND_COLOR = "#F1F8E9"

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
    .sentiment-box {{
        padding: 5px;
        border-radius: 5px;
        background-color: {SECONDARY_COLOR};
        color: white;
        font-size: 14px;
        margin-bottom: 10px;
    }}
    .metric-label {{
        font-size: 12px;
        color: #666;
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
        background-color: #E3F2FD;
    }}
    .assistant-message {{
        background-color: #F1F8E9;
    }}
    .export-button-container {{
        display: flex;
        justify-content: flex-start;
        align-items: center;
    }}
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "confidence" not in st.session_state:
    st.session_state.confidence = 5
if "importance" not in st.session_state:
    st.session_state.importance = 5
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "show_readiness_sliders" not in st.session_state:
    st.session_state.show_readiness_sliders = False
if "readiness_summary" not in st.session_state:
    st.session_state.readiness_summary = ""

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
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = [Paragraph(f"{msg['role'].capitalize()}: {msg['content']}", styles['Normal']) for msg in st.session_state.chat_history]
    doc.build(flowables)
    return buffer.getvalue()

def on_confidence_change():
    st.session_state.chat_history.append({"role": "user", "content": f"Confidence in ability to change: {st.session_state.confidence}"})
    add_message_to_thread(f"Confidence in ability to change: {st.session_state.confidence}")
    assistant_response = run_assistant()
    if assistant_response:
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

def on_importance_change():
    st.session_state.chat_history.append({"role": "user", "content": f"Importance of change: {st.session_state.importance}"})
    add_message_to_thread(f"Importance of change: {st.session_state.importance}")
    assistant_response = run_assistant()
    if assistant_response:
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

def send_message():
    user_input = st.session_state.user_input
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        add_message_to_thread(user_input)
        
        assistant_response = run_assistant()
        
        if assistant_response:
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        
        st.session_state.user_input = ""  # Clear the input

def rate_readiness():
    # Prepare the user's chat history for analysis
    user_text = " ".join(msg['content'] for msg in st.session_state.chat_history if msg['role'] == 'user')
    
    # Create a prompt to request analysis from the OpenAI assistant
    analysis_prompt = (
        "Analyze the following text for change talk and sustain talk, and provide a summary of the user's readiness to change: "
        f"{user_text}"
    )
    
    # Add the analysis request to the thread and get the response
    add_message_to_thread(analysis_prompt)
    assistant_response = run_assistant()
    
    if assistant_response:
        # Extract the summary from the assistant's response
        st.session_state.readiness_summary = assistant_response
        st.session_state.show_readiness_sliders = True

def main():
    st.title("Motivational Interviewing Chatbot")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("<h3 style='font-size: 18px;'>Metrics</h3>", unsafe_allow_html=True)
        
        if st.session_state.chat_history:
            sentiment = analyze_sentiment(" ".join(msg["content"] for msg in st.session_state.chat_history))
            st.markdown(f'<div class="sentiment-box">Sentiment: {sentiment:.2f}</div>', unsafe_allow_html=True)
        
        st.markdown('<p class="metric-label">Confidence in ability to change:</p>', unsafe_allow_html=True)
        st.slider("Confidence", 0, 10, key="confidence", on_change=on_confidence_change)
        
        st.markdown('<p class="metric-label">Importance of change:</p>', unsafe_allow_html=True)
        st.slider("Importance", 0, 10, key="importance", on_change=on_importance_change)
        
        with st.container():
            st.markdown("<div class='export-button-container'>", unsafe_allow_html=True)
            if st.button("Export to PDF", key="export_button"):
                pdf = export_to_pdf()
                st.download_button(
                    label="Download PDF",
                    data=pdf,
                    file_name="conversation_summary.pdf",
                    mime="application/pdf"
                )
            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.subheader("Chat")
        
        for message in st.session_state.chat_history:
            st.markdown(f"""
                <div class="chat-message {'user-message' if message['role'] == 'user' else 'assistant-message'}">
                    <b>{message['role'].capitalize()}:</b> {message['content']}
                </div>
            """, unsafe_allow_html=True)

        if st.session_state.readiness_summary:
            st.markdown(f"<div class='chat-message assistant-message'>{st.session_state.readiness_summary}</div>", unsafe_allow_html=True)
            st.session_state.readiness_summary = ""  # Clear the summary after displaying

        if st.session_state.show_readiness_sliders:
            st.slider("Rate your confidence from 0-10:", 0, 10, key="confidence_contextual", on_change=on_confidence_change)
            st.slider("Rate the importance from 0-10:", 0, 10, key="importance_contextual", on_change=on_importance_change)
            st.session_state.show_readiness_sliders = False

        st.text_input("Type your message here...", key="user_input")
        st.button("Send", on_click=send_message)
        st.button("Rate My Readiness to Change", on_click=rate_readiness)

if __name__ == "__main__":
    main()
