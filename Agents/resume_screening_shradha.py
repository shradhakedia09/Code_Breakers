import streamlit as st
import pdfplumber
import docx
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Helper functions ---
def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def analyze_resume_with_llm(role, resume_text):
    """Send resume text to LLM for structured analysis and scoring."""
    prompt = f"""
You are an expert HR recruiter assistant.  
A candidate is applying for the role of **{role}**.  
Below is their resume text.  

1. Extract key information:
   - Age (approx if not given)
   - Education / College
   - Key Skills
   - Projects / Experience
   - Certifications (if any)

2. For each category, explain how relevant the candidate’s background is to the role of "{role}".
   Assign a relevance score (0–10) for each category based on how closely it matches the job requirements.

3. Compute the overall weighted score using this weightage:
   - Skills: 40%
   - Projects: 30%
   - Education: 20%
   - Certifications: 10%

4. Return the result **only** in valid JSON format with these fields:
   {{
      "age": <number or null>,
      "education": <string>,
      "skills": [list of strings],
      "projects": [list of strings],
      "certifications": [list of strings],
      "score_breakdown": {{
          "skills": <int>,
          "projects": <int>,
          "education": <int>,
          "certifications": <int>
      }},
      "weighted_average": <float>,
      "verdict": "PASS" or "FAIL",
      "reasoning": <short explanation of why the candidate passed or failed>
   }}

5. Return **only** the JSON object. Do not include any other commentary or text.

Resume Text:
\"\"\"{resume_text}\"\"\"
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        temperature=0.3
    )
    return response.output_text


# --- Streamlit UI ---
st.title("🧠 AI Resume Screener")
st.write("An AI-powered tool that screens resumes based on the role you’re applying for.")

# Ask for the role
role = st.text_input("💼 What role are you applying for? (e.g., Data Analyst, Frontend Developer)")

# Mock vacancy check (for demo)
if role:
    if role.lower() in ["hr intern"]:  # simulate "no vacancy" example
        st.error(f"❌ Sorry, there is currently no vacancy for '{role}'.")
    else:
        st.success(f"✅ Vacancy available for '{role}'! Please upload your resume below:")
        
        uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
        
        if uploaded_file is not None:
            # Extract text
            with st.spinner("Reading your resume..."):
                if uploaded_file.name.endswith(".pdf"):
                    resume_text = extract_text_from_pdf(uploaded_file)
                else:
                    resume_text = extract_text_from_docx(uploaded_file)
            
            if resume_text.strip():
                with st.spinner("Analyzing resume..."):
                    llm_output = analyze_resume_with_llm(role, resume_text)
                
                import json

                st.subheader("📊 Screening Results")

                try:
                    # Try to parse LLM text into valid JSON
                    parsed_output = json.loads(llm_output)
                    st.json(parsed_output)
                except json.JSONDecodeError:
                    st.warning("⚠️ The AI response wasn’t in perfect JSON format. Showing raw output instead:")
                    st.text(llm_output)

            else:
                st.error("⚠️ Could not extract text from the uploaded file. Please upload a clearer copy.")
