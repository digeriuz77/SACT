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

# 8-bit pixel avatar (you can replace this with an actual image URL)
AVATAR_HTML = """
<svg class="avatar" viewBox="0 0 100 100">
    <rect x="0" y="0" width="100" height="100" fill="#FFD700"/>
    <rect x="30" y="30" width="15" height="15" fill="#000000"/>
    <rect x="55" y="30" width="15" height="15" fill="#000000"/>
    <rect x="40" y="60" width="20" height="10" fill="#FF0000"/>
</svg>
"""

# Initialize session state
def init_session_state():
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
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False

# Call the initialization function
init_session_state()

# Initialize OpenAI client with v2 beta header
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"],
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

# Assistant ID for DecisionBalanceandPlan
ASSISTANT_ID = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"

# ... (keep the existing functions: create_thread_if_not_exists, add_message_to_thread, run_assistant, analyze_sentiment, export_to_pdf)

def display_chat_history():
    for message in st.session_state.chat_history:
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar=AVATAR_HTML):
                st.write(message["content"])
        else:
            with st.chat_message("user"):
                st.write(message["content"])

def get_initial_question():
    questions = [
        "So, what's next for you?",
        "So, where do you go from here?",
        "So, what do you think you will do?",
        "So, what are you going to do?"
    ]
    return random.choice(questions)

def main():
    st.title("Motivational Interviewing Chatbot")

    # Create a layout with two columns
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Metrics")
        
        # Sentiment analysis in a small box
        if st.session_state.chat_history:
            all_text = " ".join([msg["content"] for msg in st.session_state.chat_history])
            sentiment = analyze_sentiment(all_text)
            st.markdown(f"""
                <div class="sentiment-box">
                    Overall Sentiment: {sentiment:.2f}
                </div>
            """, unsafe_allow_html=True)
        
        # Persistent sliders
        st.write("How confident are you in your ability to make this change?")
        st.session_state.confidence = st.slider("Confidence", 0, 10, st.session_state.confidence)
        
        st.write("How important is this change to you?")
        st.session_state.importance = st.slider("Importance", 0, 10, st.session_state.importance)
        
        # Export to PDF button
        if st.button("Export Conversation to PDF"):
            pdf = export_to_pdf()
            st.download_button(
                label="Download PDF",
                data=pdf,
                file_name="conversation_summary.pdf",
                mime="application/pdf"
            )

    with col2:
        # Main chat area
        st.subheader("Chat")
        chat_container = st.container()

        with chat_container:
            display_chat_history()

            # Start the conversation if it hasn't started yet
            if not st.session_state.conversation_started:
                initial_message = "I'm here to help you make a change. " + get_initial_question()
                st.session_state.chat_history.append({"role": "assistant", "content": initial_message})
                add_message_to_thread(initial_message)
                st.session_state.conversation_started = True
                st.experimental_rerun()

            # User input
            user_input = st.chat_input("Type your message here...")

            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                add_message_to_thread(user_input)
                assistant_response = run_assistant()
                if assistant_response:
                    st.experimental_rerun()
                else:
                    st.error("Failed to get a response from the assistant. Please try again.")

if __name__ == "__main__":
    main()
