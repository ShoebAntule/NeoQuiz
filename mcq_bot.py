import os
import streamlit as st
from openai import OpenAI
import re

# Set your API key securely
from dotenv import load_dotenv
load_dotenv()
import os

# Initialize OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("OPENAI_API_KEY"),
)

def generate_mcqs(subject, num_questions=5):
    prompt = f"""
Generate {num_questions} multiple-choice questions on the topic "{subject}".
Each question should follow this format:

Q1. [Question]
a) Option A
b) Option B
c) Option C
d) Option D
Answer: [Correct Option Letter]

Please follow this format for all questions.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in creating MCQs for educational subjects."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500,
    )
    return response.choices[0].message.content.strip()

def split_mcqs(mcq_text):
    # Split MCQs using regex pattern: starts with Q followed by number and a period
    pattern = r"(Q\d+\..*?Answer: [a-dA-D])(?=\nQ\d+\.|\Z)"
    return re.findall(pattern, mcq_text, flags=re.DOTALL)

# Streamlit App
st.set_page_config(page_title="MCQ Generator", page_icon="📘", layout="centered")
st.title("📘 NEOQUIZ Generator")
st.write("Enter a topic and generate multiple-choice questions with copy buttons.")

subject = st.text_input("📚 Subject/Topic:")
num_questions = st.selectbox("🔢 Number of Questions", [5, 6, 7, 8, 9, 10])

if st.button("🚀 Generate MCQs"):
    if subject.strip() == "":
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Generating questions..."):
            mcq_text = generate_mcqs(subject, num_questions)
            mcq_list = split_mcqs(mcq_text)

        st.success("✅ MCQs generated successfully!")

        for i, mcq in enumerate(mcq_list, 1):
            st.markdown(f"### 🧾 Question {i}")
            st.code(mcq, language="markdown")

            # Custom JS button to copy that block
            copy_button_id = f"copy_button_{i}"
            st.markdown(f"""
            <button onclick="navigator.clipboard.writeText(`{mcq}`)"
            id="{copy_button_id}"
            style="background-color:#4CAF50;border:none;color:white;padding:8px 16px;
            font-size:14px;margin-bottom:20px;border-radius:6px;cursor:pointer;">
            📋 Copy This Question
            </button>
            """, unsafe_allow_html=True)

        # Optional download of all questions
        st.download_button(
            label="📥 Download All as .txt",
            data=mcq_text,
            file_name=f"{subject.replace(' ', '_')}_MCQs.txt",
            mime="text/plain"
        )
