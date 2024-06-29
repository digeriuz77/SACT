import streamlit as st
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
from transformers import pipeline
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Set Streamlit page configuration
st.set_page_config(page_title='Motivational Interviewing Chatbot', layout='wide')

# Initialize session states
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "step" not in st.session_state:
    st.session_state["step"] = 0
if "confidence" not in st.session_state:
    st.session_state["confidence"] = 0
if "importance" not in st.session_state:
    st.session_state["importance"] = 0
if "change_goal" not in st.session_state:
    st.session_state["change_goal"] = ""

def get_user_name():
    user_name = st.text_input("Before we begin, what's your name?")
    if user_name:
        st.session_state["user_name"] = user_name
        st.session_state["step"] = 1
        st.experimental_rerun()

def confidence_importance_ruler():
    st.write(f"Hello {st.session_state['user_name']}, let's start by assessing your confidence and the importance of the change you want to make.")
    st.session_state["change_goal"] = st.text_input("What change are you considering?")
    st.session_state["confidence"] = st.slider("On a scale of 0-10, how confident are you in your ability to make this change?", 0, 10, 5)
    st.session_state["importance"] = st.slider("On a scale of 0-10, how important is this change to you?", 0, 10, 5)
    
    if st.button("Continue"):
        st.session_state["step"] = 2
        st.experimental_rerun()

def ask_ruler_questions():
    st.write(f"Thank you for sharing, {st.session_state['user_name']}. Let's explore your answers a bit more.")
    
    confidence_why = st.text_area(f"Why are you a {st.session_state['confidence']} on the confidence scale and not a zero?")
    confidence_increase = st.text_area(f"What would it take for you to get from {st.session_state['confidence']} to {min(st.session_state['confidence']+1, 10)} on the confidence scale?")
    
    importance_why = st.text_area(f"Why are you a {st.session_state['importance']} on the importance scale and not a zero?")
    importance_increase = st.text_area(f"What would it take for you to get from {st.session_state['importance']} to {min(st.session_state['importance']+1, 10)} on the importance scale?")
    
    if st.button("Continue to Key Question"):
        st.session_state["ruler_responses"] = {
            "confidence_why": confidence_why,
            "confidence_increase": confidence_increase,
            "importance_why": importance_why,
            "importance_increase": importance_increase
        }
        st.session_state["step"] = 3
        st.experimental_rerun()

def ask_key_question():
    key_questions = [
        "So, what's next for you?",
        "So, where do you go from here?",
        "So, what do you think you will do?",
        "So, what are you going to do?"
    ]
    question = random.choice(key_questions)
    st.write(f"{st.session_state['user_name']}, {question}")
    response = st.text_area("Your response:")
    if st.button("Continue to Planning"):
        st.session_state["key_question_response"] = response
        st.session_state["step"] = 4
        st.experimental_rerun()

def make_plan():
    st.write(f"Great, {st.session_state['user_name']}! Let's create a plan for your change.")
    
    initial_steps = st.text_area("What are the initial steps you'll take to start your plan?")
    important_focus = st.text_area("What are the 2-3 most important things to focus on to make your plan a success?")
    support_system = st.text_area("Who might help you in making this change?")
    assistance_needed = st.text_area("How can I (as your AI coach) help you successfully make this change?")
    future_conversations = st.text_area("When and how would you like to have follow-up conversations about your progress?")
    
    if st.button("Finish Plan"):
        st.session_state["plan"] = {
            "initial_steps": initial_steps,
            "important_focus": important_focus,
            "support_system": support_system,
            "assistance_needed": assistance_needed,
            "future_conversations": future_conversations
        }
        st.session_state["step"] = 5
        st.experimental_rerun()

def summarize_session():
    all_text = (
        f"Change Goal: {st.session_state['change_goal']}\n"
        f"Confidence: {st.session_state['confidence']}/10\n"
        f"Importance: {st.session_state['importance']}/10\n"
        f"Confidence Why: {st.session_state['ruler_responses']['confidence_why']}\n"
        f"Confidence Increase: {st.session_state['ruler_responses']['confidence_increase']}\n"
        f"Importance Why: {st.session_state['ruler_responses']['importance_why']}\n"
        f"Importance Increase: {st.session_state['ruler_responses']['importance_increase']}\n"
        f"Key Question Response: {st.session_state['key_question_response']}\n"
        f"Plan:\n"
        f"  Initial Steps: {st.session_state['plan']['initial_steps']}\n"
        f"  Important Focus: {st.session_state['plan']['important_focus']}\n"
        f"  Support System: {st.session_state['plan']['support_system']}\n"
        f"  Assistance Needed: {st.session_state['plan']['assistance_needed']}\n"
        f"  Future Conversations: {st.session_state['plan']['future_conversations']}\n"
    )
    
    summary = summarizer(all_text, max_length=300, min_length=100, do_sample=False)[0]['summary_text']
    
    st.write("Here's a summary of our conversation:")
    st.write(summary)
    
    if st.button("Reassess Confidence and Importance"):
        st.session_state["step"] = 1
        st.experimental_rerun()
    
    email = st.text_input("If you'd like to receive this summary by email, please enter your email address:")
    if email and st.button("Send Summary"):
        send_email(email, summary)
        st.write("Summary sent to your email!")

def send_email(to_email, summary):
    # This is a placeholder function. In a real application, you'd need to set up a proper email sending service.
    st.write(f"Email sending simulation: Sending summary to {to_email}")
    st.write("Summary content:")
    st.write(summary)

def main():
    st.title("Motivational Interviewing Chatbot")
    
    if st.session_state["step"] == 0:
        get_user_name()
    elif st.session_state["step"] == 1:
        confidence_importance_ruler()
    elif st.session_state["step"] == 2:
        ask_ruler_questions()
    elif st.session_state["step"] == 3:
        ask_key_question()
    elif st.session_state["step"] == 4:
        make_plan()
    elif st.session_state["step"] == 5:
        summarize_session()

if __name__ == "__main__":
    main()
