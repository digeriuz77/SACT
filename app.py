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

# ... (previous code remains the same)

def run_assistant(instructions=None):
    create_thread_if_not_exists()
    try:
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            instructions=instructions
        )
        
        while True:
            try:
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
            except Exception as e:
                st.error(f"Error retrieving run status: {str(e)}")
                return None
        
        try:
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            
            assistant_message = messages.data[0].content[0].text.value
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            st.error(f"Error retrieving messages: {str(e)}")
            return None
    except Exception as e:
        st.error(f"Error creating run: {str(e)}")
        return None

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
            if assistant_response:
                st.experimental_rerun()
            else:
                st.error("Failed to get a response from the assistant. Please try again.")

    # ... (rest of the main function remains the same)

if __name__ == "__main__":
    main()
