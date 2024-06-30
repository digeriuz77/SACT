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
import re

# ... [Previous imports and initializations remain the same]

# Add this new function to check for exit condition
def check_for_exit_condition(text):
    return "exit the chat" in text.lower()

# Modify the main function
def main():
    st.title("Motivational Interviewing Chatbot")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("<h3 style='font-size: 18px;'>Metrics</h3>", unsafe_allow_html=True)
        
        if st.session_state.chat_history:
            sentiment = analyze_sentiment(" ".join(msg["content"] for msg in st.session_state.chat_history))
            st.markdown(f'<div class="sentiment-box">Sentiment: {sentiment:.2f}</div>', unsafe_allow_html=True)
        
        # Show the "Rate my readiness to change" button only when prompted
        if st.session_state.show_readiness_button:
            st.button("Rate my readiness to change", on_click=rate_readiness, key="rate_readiness", type="primary")

    with col2:
        st.subheader("Chat")
        
        for message in st.session_state.chat_history:
            st.markdown(f"""
                <div class="chat-message {'user-message' if message['role'] == 'user' else 'assistant-message'}">
                    <b>{message['role'].capitalize()}:</b> {message['content']}
                </div>
            """, unsafe_allow_html=True)
            
            # Display sliders after assistant messages if conditions are met
            if message['role'] == 'assistant' and st.session_state.show_slider:
                confidence = st.slider("Confidence in ability to change:", 0, 10, st.session_state.confidence, key=f"confidence_{len(st.session_state.chat_history)}")
                importance = st.slider("Importance of change:", 0, 10, st.session_state.importance, key=f"importance_{len(st.session_state.chat_history)}")
                
                if confidence != st.session_state.confidence:
                    st.session_state.confidence = confidence
                    on_confidence_change()
                
                if importance != st.session_state.importance:
                    st.session_state.importance = importance
                    on_importance_change()
            
            # Display Export PDF button if exit condition is met
            if message['role'] == 'assistant' and check_for_exit_condition(message['content']):
                pdf = export_to_pdf()
                st.download_button(
                    label="Export Chat to PDF",
                    data=pdf,
                    file_name="conversation_summary.pdf",
                    mime="application/pdf"
                )

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
                st.session_state.show_slider = check_for_slider_condition(assistant_response)
                st.session_state.show_summary_options = check_for_summary_condition(assistant_response)
                st.session_state.show_readiness_button = check_for_readiness_review(assistant_response)
            
            st.experimental_rerun()

# ... [Rest of the code remains the same]

if __name__ == "__main__":
    main()
