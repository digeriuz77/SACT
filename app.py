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

# ... (keep the previous imports and configuration code)

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
    if "assistant_id" not in st.session_state:
        st.session_state.assistant_id = None

# Call the initialization function
init_session_state()

# Initialize OpenAI client with v2 beta header
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"],
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

def create_or_update_assistant():
    assistant_name = "Motivational Interviewing Assistant"
    model = "gpt-3.5-turbo-0125"
    instructions = """You are a motivational interviewing assistant. Your role is to help users explore their readiness to change, 
    increase their motivation, and develop a plan for change. Use open-ended questions, reflective listening, and affirmations. 
    Focus on eliciting change talk and helping the user resolve ambivalence about change."""

    try:
        if st.session_state.assistant_id:
            assistant = client.beta.assistants.update(
                assistant_id=st.session_state.assistant_id,
                name=assistant_name,
                instructions=instructions,
                model=model,
                tools=[{"type": "code_interpreter"}]
            )
        else:
            assistant = client.beta.assistants.create(
                name=assistant_name,
                instructions=instructions,
                model=model,
                tools=[{"type": "code_interpreter"}]
            )
        st.session_state.assistant_id = assistant.id
        return assistant
    except Exception as e:
        st.error(f"Error creating/updating assistant: {str(e)}")
        return None

# ... (keep the existing functions: create_thread_if_not_exists, add_message_to_thread, analyze_sentiment, export_to_pdf, display_chat_history, get_initial_question)

def run_assistant(instructions=None):
    create_thread_if_not_exists()
    try:
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=st.session_state.assistant_id,
            instructions=instructions
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
        
        assistant_message = messages.data[0].content[0].text.value
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})
        return assistant_message
    except Exception as e:
        st.error(f"Error in run_assistant: {str(e)}")
        return None

def main():
    st.title("Motivational Interviewing Chatbot")

    # Create or update the assistant
    assistant = create_or_update_assistant()
    if not assistant:
        st.error("Failed to create or update the assistant. Please check your API key and try again.")
        return

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
