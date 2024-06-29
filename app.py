import streamlit as st
import openai
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
import time
from langchain.memory import ConversationBufferMemory

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)

# Set Streamlit page configuration
st.set_page_config(page_title='Motivational Interviewing Chatbot', layout='wide')

# Initialize session states
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "user_inputs" not in st.session_state:
    st.session_state.user_inputs = {}
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "openai_client" not in st.session_state:
    st.session_state.openai_client = None

# OpenAI Assistant ID (replace with your actual Assistant ID)
ASSISTANT_ID = "asst_your_assistant_id_here"

def initialize_openai_client():
    api_key = st.secrets["openai_api_key"]
    st.session_state.openai_client = openai.OpenAI(api_key=api_key)
    # Create a thread for the conversation
    thread = st.session_state.openai_client.beta.threads.create()
    st.session_state.thread_id = thread.id

def get_ai_response(user_input):
    if not st.session_state.thread_id:
        initialize_openai_client()
    
    # Add the user's message to the thread
    st.session_state.openai_client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    # Create a run
    run = st.session_state.openai_client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Wait for the run to complete
    while run.status != 'completed':
        time.sleep(1)
        run = st.session_state.openai_client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )

    # Retrieve the assistant's response
    messages = st.session_state.openai_client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    assistant_message = next(msg for msg in messages if msg.role == "assistant")
    return assistant_message.content[0].text.value

def sentiment_analysis(text):
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)['compound']

def analyze_change_talk(text):
    change_talk_categories = {
        "Desire": ["want to", "would like to", "wish"],
        "Ability": ["could", "can", "might be able to"],
        "Reasons": ["would probably", "need to"],
        "Need": ["ought to", "have to", "should"],
        "Commitment": ["am going to", "promise", "intend to"],
        "Activation": ["am ready to", "will start"],
        "Taking Steps": ["actually went", "started"]
    }
    
    results = {}
    for category, phrases in change_talk_categories.items():
        matches = [phrase for phrase in phrases if phrase in text.lower()]
        if matches:
            results[category] = matches
    
    return results

def get_user_name():
    user_name = st.text_input("Before we begin, what's your name?")
    if user_name:
        st.session_state.user_inputs['name'] = user_name
        st.session_state.current_step = 1
        st.experimental_rerun()

def confidence_importance_ruler():
    st.write(f"Hello {st.session_state.user_inputs['name']}, let's assess your confidence and the importance of the change you want to make.")
    
    change_goal = st.text_input("What change are you considering?", key="change_goal")
    confidence = st.slider("On a scale of 0-10, how confident are you in your ability to make this change?", 0, 10, 5, key="confidence")
    importance = st.slider("On a scale of 0-10, how important is this change to you?", 0, 10, 5, key="importance")
    
    if st.button("Continue", key="ruler_continue"):
        st.session_state.user_inputs['change_goal'] = change_goal
        st.session_state.user_inputs['confidence'] = confidence
        st.session_state.user_inputs['importance'] = importance
        st.session_state.current_step = 2
        st.experimental_rerun()

def ask_ruler_questions():
    st.write(f"Thank you for sharing, {st.session_state.user_inputs['name']}. Let's explore your answers a bit more.")
    
    confidence_why = st.text_area(f"Why are you a {st.session_state.user_inputs['confidence']} on the confidence scale and not a zero?", key="confidence_why")
    confidence_increase = st.text_area(f"What would it take for you to get from {st.session_state.user_inputs['confidence']} to {min(st.session_state.user_inputs['confidence']+1, 10)} on the confidence scale?", key="confidence_increase")
    
    importance_why = st.text_area(f"Why are you a {st.session_state.user_inputs['importance']} on the importance scale and not a zero?", key="importance_why")
    importance_increase = st.text_area(f"What would it take for you to get from {st.session_state.user_inputs['importance']} to {min(st.session_state.user_inputs['importance']+1, 10)} on the importance scale?", key="importance_increase")
    
    if st.button("Continue to Key Question", key="ruler_questions_continue"):
        st.session_state.user_inputs['confidence_why'] = confidence_why
        st.session_state.user_inputs['confidence_increase'] = confidence_increase
        st.session_state.user_inputs['importance_why'] = importance_why
        st.session_state.user_inputs['importance_increase'] = importance_increase
        st.session_state.current_step = 3
        st.experimental_rerun()

def ask_key_question():
    key_question = get_ai_response(f"Generate a key question to help {st.session_state.user_inputs['name']} determine their next steps regarding their goal: {st.session_state.user_inputs['change_goal']}")
    st.write(f"{st.session_state.user_inputs['name']}, {key_question}")
    response = st.text_area("Your response:", key="key_question_response")
    if st.button("Continue to Planning", key="key_question_continue"):
        st.session_state.user_inputs['key_question_response'] = response
        st.session_state.current_step = 4
        st.experimental_rerun()

def make_plan():
    st.write(f"Great, {st.session_state.user_inputs['name']}! Let's create a plan for your change.")
    
    plan_prompt = f"Create a structured plan for {st.session_state.user_inputs['name']} to achieve their goal of {st.session_state.user_inputs['change_goal']}. Include initial steps, important focus areas, potential support system, and how you (as an AI coach) can assist."
    ai_plan = get_ai_response(plan_prompt)
    
    st.write("Here's a suggested plan based on our conversation:")
    st.write(ai_plan)
    
    user_plan = st.text_area("Feel free to modify this plan or write your own:", value=ai_plan, height=300, key="user_plan")
    
    if st.button("Finish Plan", key="finish_plan"):
        st.session_state.user_inputs['plan'] = user_plan
        st.session_state.current_step = 5
        st.experimental_rerun()

def summarize_session():
    all_text = "\n".join(str(value) for value in st.session_state.user_inputs.values())
    
    sentiment_score = sentiment_analysis(all_text)
    change_talk = analyze_change_talk(all_text)
    
    summary_prompt = f"Summarize the conversation with {st.session_state.user_inputs['name']} about their goal to {st.session_state.user_inputs['change_goal']}. Include insights on their confidence, importance, and plan."
    ai_summary = get_ai_response(summary_prompt)
    
    st.write("Here's a summary of our conversation:")
    st.write(ai_summary)
    
    st.write("\nChange Talk Analysis:")
    for category, phrases in change_talk.items():
        st.write(f"{category}: {', '.join(phrases)}")
    
    st.write(f"\nOverall Sentiment: {sentiment_score:.2f} (-1 to 1 scale)")
    
    if st.button("Reassess Confidence and Importance", key="reassess"):
        st.session_state.current_step = 1
        st.experimental_rerun()
    
    email = st.text_input("If you'd like to receive this summary by email, please enter your email address:", key="email")
    if email and st.button("Send Summary", key="send_summary"):
        # Implement email sending functionality here
        st.write("Summary sent to your email!")

def main():
    st.title("Motivational Interviewing Chatbot")
    
    steps = [get_user_name, confidence_importance_ruler, ask_ruler_questions, ask_key_question, make_plan, summarize_session]
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    for i, step_func in enumerate(steps):
        if st.sidebar.button(f"Step {i+1}: {step_func.__name__}", key=f"nav_{i}"):
            st.session_state.current_step = i
    
    # Main content
    current_step = st.session_state.current_step
    steps[current_step]()
    
    # Progress bar
    st.progress((current_step + 1) / len(steps))

if __name__ == "__main__":
    main()
