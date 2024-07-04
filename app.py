import streamlit as st
import openai
from openai import OpenAI
import time
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import random
import json
from datetime import datetime
import os
import base64
import plotly.graph_objects as go
import re
from collections import Counter


# Initialize logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize NLTK
nltk.download('vader_lexicon', quiet=True)

# Streamlit configuration
st.set_page_config(page_title="✨ VHL Change Coachbot", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .user-message {
        background-color: white;
        color: black;
        border-radius: 20px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 70%;
        align-self: flex-start;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .assistant-message {
        background-color: #007bff;
        color: white;
        border-radius: 20px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 70%;
        align-self: flex-end;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .message-container {
        display: flex;
        flex-direction: column;
    }
</style>
""", unsafe_allow_html=True)

# Load the change talk data
with open('change_talk.json', 'r') as f:
    change_talk_data = [json.loads(line) for line in f]

# Create a dictionary mapping statements to stages
change_talk_dict = {item['statement'].lower(): item['stage'] for item in change_talk_data if item['statement']}

def analyze_change_talk(text):
    sentences = re.split(r'[.!?]+', text.lower())
    stage_counts = Counter()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence in change_talk_dict:
            stage = change_talk_dict[sentence]
            stage_counts[stage] += 1
        else:
            for statement, stage in change_talk_dict.items():
                if statement in sentence:
                    stage_counts[stage] += 1
                    break
    
    total_statements = sum(stage_counts.values())
    if total_statements == 0:
        return 0, {}
    
    stage_weights = {
        'pre': 0,
        'contemplation': 1,
        'planning': 2,
        'action': 3,
        'maintenance': 4
    }
    
    weighted_sum = sum(stage_weights[stage] * count for stage, count in stage_counts.items())
    change_talk_score = weighted_sum / total_statements
    normalized_score = change_talk_score / max(stage_weights.values())
    stage_percentages = {stage: (count / total_statements) * 100 for stage, count in stage_counts.items()}
    
    return normalized_score, stage_percentages

# Initialize session state
def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "current_assistant_id" not in st.session_state:
        st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"
    if "welcome_message_displayed" not in st.session_state:
        st.session_state.welcome_message_displayed = True
    if "saved_chats" not in st.session_state:
        st.session_state.saved_chats = []

initialize_session_state()

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

def stream_response(response):
    full_response = ""
    for chunk in response.split():
        full_response += chunk + " "
        yield full_response

def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)['compound']

def analyze_change_talk(text):
    # Simplified keywords for each stage
    stages = {
        'pre': ['don\'t', 'won\'t', 'can\'t', 'not', 'never', 'no'],
        'contemplation': ['might', 'maybe', 'consider', 'possibly'],
        'planning': ['plan', 'intend', 'will', 'going to'],
        'action': ['doing', 'started', 'began', 'implemented'],
        'maintenance': ['continuing', 'maintaining', 'kept', 'sustained']
    }
    
    words = re.findall(r'\w+', text.lower())
    stage_counts = Counter()

    for word in words:
        for stage, keywords in stages.items():
            if word in keywords:
                stage_counts[stage] += 1
    
    total = sum(stage_counts.values())
    if total == 0:
        return {stage: 0 for stage in stages}, 0

    percentages = {stage: (count / total) * 100 for stage, count in stage_counts.items()}
    
    # Calculate a simple score (higher stages have more weight)
    score = sum(i * count for i, (stage, count) in enumerate(stage_counts.items())) / total
    normalized_score = score / (len(stages) - 1)  # Normalize to 0-1 range

    return percentages, normalized_score

def rate_readiness():
    st.session_state.current_assistant_id = "asst_u4tbCd0KubyMYfKeD59bBxjM"
    save_chat()  # Save chat to create the log file
    chat_log = " ".join([msg['content'] for msg in st.session_state.chat_history if msg['role'] == 'user'])
    
    # Analyze change talk locally
    stage_percentages, change_talk_score = analyze_change_talk(chat_log)
    
    # Visualize change talk score and stage percentages
    st.subheader("Change Talk Analysis")
    st.write(f"Overall Change Talk Score: {change_talk_score:.2f}")
    
    # Create a bar chart for stage percentages
    fig = go.Figure(data=[go.Bar(x=list(stage_percentages.keys()), y=list(stage_percentages.values()))])
    fig.update_layout(title='Stages of Change Distribution',
                      xaxis_title='Stage',
                      yaxis_title='Percentage')
    st.plotly_chart(fig)
    
    # Get AI assistant's analysis
    add_message_to_thread(f"Review the following chat log for change talk and provide a summary of the user's readiness to change:\n{chat_log}")
    assistant_response = run_assistant()
    
    if assistant_response:
        st.subheader("AI Assistant's Analysis")
        st.write(assistant_response)
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
    
    st.session_state.current_assistant_id = "asst_RAJ5HUmKrqKXAoBDhacjvMy8"  # Reset to main assistant
    
def summarize_conversation():
    st.session_state.current_assistant_id = "asst_2IN1dkowoziRpYyzSdgJbPZY"
    save_chat()  # Save chat to create the log file
    chat_log = " ".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history])
    add_message_to_thread(f"Please summarize the following chat log:\n{chat_log}")
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
    chat_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "chat_history": st.session_state.chat_history
    }
    st.session_state.saved_chats.append(chat_data)
    st.success(f"Chat history saved")

def get_saved_chats():
    return st.session_state.saved_chats

def load_chat(chat_data):
    st.session_state.chat_history = chat_data['chat_history']
    st.session_state.welcome_message_displayed = True
    st.experimental_rerun()

def export_chat():
    chat_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])
    b64 = base64.b64encode(chat_text.encode()).decode()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_export_{timestamp}.txt"
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download Chat History</a>'
    return href

def show_info():
    st.markdown("""
    <div style="padding: 10px; border-radius: 5px; background-color: #007bff; color: white;">
    <p>The VHL Make-a-change Coachbot is written by Gary Stanyard of Virtual Health Labs.</p>
    <p>You can find out more about VHL here: <a href="https://strategichealth.kartra.com/page/Coachbot" target="_blank" style="color: white;">VHL</a></p>
    </div>
    """, unsafe_allow_html=True)

welcome_messages = [
    "Hi there! I'm a coach specializing in motivational interviewing. What change are you considering?",
    "Hello! I'm here to guide you through the process of change. What would you like to focus on today?",
    "Welcome! As a motivational interviewing coach, I'm here to support you. What change are you thinking about making?"
]

def main():
    st.title("✨VHL Change Coachbot")

    # Choose a random welcome message for the subheader if not already set
    if "welcome_subheader" not in st.session_state:
        st.session_state.welcome_subheader = random.choice(welcome_messages)

    # Initialize toggle state if not exists
    if 'show_info' not in st.session_state:
        st.session_state.show_info = False

    # Info button as a toggle
    if st.button("ℹ️ About", help="Click to toggle information"):
        st.session_state.show_info = not st.session_state.show_info

    # Display info if toggle is True
    if st.session_state.show_info:
        show_info()

    # Create containers
    chat_container = st.container()
    streaming_container = st.container()
    input_container = st.container()
    controls_container = st.container()

    with chat_container:
        st.subheader(st.session_state.welcome_subheader)
        
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            if message['role'] == 'assistant':
                st.markdown(f'<div class="message-container" style="display: flex; justify-content: flex-end;"><div class="assistant-message">{message["content"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message-container" style="display: flex; justify-content: flex-start;"><div class="user-message">{message["content"]}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with input_container:
        user_input = st.chat_input("Type your message...", key="user_input")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            add_message_to_thread(user_input)

            with st.spinner("Thinking..."):
                assistant_response = run_assistant()

            if assistant_response:
                with streaming_container:
                    message_placeholder = st.empty()
                    full_response = ""
                    for chunk in stream_response(assistant_response):
                        message_placeholder.markdown(f'<div class="message-container" style="display: flex; justify-content: flex-end;"><div class="assistant-message">{chunk}</div></div>', unsafe_allow_html=True)
                        time.sleep(0.05)
                    full_response = chunk
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})

            st.experimental_rerun()

    with controls_container:
        if st.session_state.get("chat_history"):
            sentiment = analyze_sentiment(" ".join(msg["content"] for msg in st.session_state["chat_history"]))
            st.write(f'Sentiment: {sentiment:.2f}')

        # Buttons for functionality in a row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("Start Over"):
                reset_chat()
        with col2:
            if st.button("Save Chat"):
                save_chat()
        with col3:
            if st.button("Summarize"):
                summarize_conversation()
        with col4:
            if st.button("Review Readiness"):
                rate_readiness()
        with col5:
            st.markdown(export_chat(), unsafe_allow_html=True)

        # Saved chats dropdown
        saved_chats = get_saved_chats()
        if saved_chats:
            selected_chat = st.selectbox(
                "Load a saved chat",
                options=saved_chats,
                format_func=lambda x: x['timestamp']
            )
            if st.button("Load Selected Chat"):
                load_chat(selected_chat)

if __name__ == "__main__":
    main()
