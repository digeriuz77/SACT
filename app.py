import streamlit as st
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)

def sentiment_analysis(text):
    sia = SentimentIntensityAnalyzer()
    score = sia.polarity_scores(text)['compound']
    return score

def interpret_score(score):
    if score >= 0.05:
        return "Positive sentiment: You seem to be in a good state of preparedness to change."
    elif score <= -0.05:
        return "Negative sentiment: You may be experiencing some anxiety about change. Consider your goals."
    else:
        return "Neutral sentiment: Your responses indicate a balanced view. It might be helpful to explore your feelings further."

def identify_change_talk(text):
    change_talk_patterns = [
        r'\b(want|need|desire|hope)\b.*\bto change\b',
        r'\b(can|could|able)\b.*\bchange\b',
        r'\b(will|going to|plan)\b.*\bchange\b',
        r'\b(reason|benefit|advantage)\b.*\bchange\b'
    ]
    
    change_talk = []
    sentences = nltk.sent_tokenize(text)
    
    for sentence in sentences:
        for pattern in change_talk_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                change_talk.append(sentence)
                break
    
    return change_talk

def analyze_responses(responses):
    all_text = " ".join(responses)
    sentiment_score = sentiment_analysis(all_text)
    interpretation = interpret_score(sentiment_score)
    change_talk = identify_change_talk(all_text)
    
    return sentiment_score, interpretation, change_talk

def generate_plan(sentiment_score, change_talk):
    plan_steps = []
    
    # Open question
    plan_steps.append({
        "step_number": 1,
        "step_type": "open_question",
        "content": "What specific change are you considering making in your life?"
    })
    
    # Affirmation based on sentiment
    if sentiment_score >= 0.05:
        plan_steps.append({
            "step_number": 2,
            "step_type": "affirmation",
            "content": "Your positive outlook is a great foundation for making changes. Well done!"
        })
    else:
        plan_steps.append({
            "step_number": 2,
            "step_type": "affirmation",
            "content": "Recognizing the need for change is an important first step. You're on the right track."
        })
    
    # Reflection on change talk
    if change_talk:
        plan_steps.append({
            "step_number": 3,
            "step_type": "reflection",
            "content": f"I noticed you mentioned '{change_talk[0]}'. Can you elaborate on that?"
        })
    
    # Plan details
    plan_steps.append({
        "step_number": 4,
        "step_type": "plan_detail",
        "content": "Let's outline some initial steps you can take to start your change journey."
    })
    
    return plan_steps

st.title("Readiness to Change Analyzer")
st.write("Please answer the following questions honestly. All responses are confidential.")

questions = [
    "How do you feel about making a change in your life right now?",
    "What are some reasons you might want to make a change?",
    "What steps have you already taken, if any, towards making a change?",
    "What challenges do you foresee in making this change?",
    "Who might support you in making this change?"
]

responses = [st.text_area(question) for question in questions]

if st.button("Analyze My Responses"):
    if all(response.strip() != "" for response in responses):
        sentiment_score, interpretation, change_talk = analyze_responses(responses)
        
        st.write(f"**Sentiment Analysis:** {interpretation}")
        
        if change_talk:
            st.write("**Change Talk Identified:**")
            for talk in change_talk:
                st.write(f"- {talk}")
        else:
            st.write("No specific change talk identified. Consider exploring your motivations further.")
        
        st.write("**Personalized Plan:**")
        plan_steps = generate_plan(sentiment_score, change_talk)
        for step in plan_steps:
            st.write(f"{step['step_number']}. [{step['step_type'].capitalize()}] {step['content']}")
        
        st.write("\n**Important:**")
        st.write("- This tool is for self-assessment purposes only and cannot replace professional guidance.")
        st.write("- If you are concerned about your mental health or need additional support, please seek help from a qualified professional.")
    else:
        st.write("Please answer all questions before analyzing.")
