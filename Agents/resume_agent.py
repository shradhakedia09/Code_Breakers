import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WEIGHTS = {
    "cgpa": 0.3,
    "projects": 0.3,
    "experience": 0.4
}



def evaluate_resume(resume_text, job_description):
    prompt = f"""
    You are an HR resume evaluator.

    Extract the following details from the resume and evaluate the candidate:

    1. name — Full name of the candidate  
    2. email — Candidate's email address  
    3. department — If mentioned, extract or infer likely department or field (e.g., HR, Data Science, Marketing)  
    4. cgpa — 0–100 score for academic record
    5. projects — 0–100 score for project quality
    6. experience — 0–100 score for previous experience relevance

    Return ONLY valid JSON in this format:
    {{
        "name": "John Doe",
        "email": "john@example.com",
        "department": "HR",
        "scores": {{"cgpa": 85, "projects": 90, "experience": 88}}
    }}

    JOB DESCRIPTION:
    {job_description}

    RESUME:
    {resume_text}
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = resp.choices[0].message.content.strip()
    print("\nMODEL RESPONSE:\n", content)

    import json, re
    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            data = {"name": None, "email": None, "department": None, "scores": {"cgpa": 0, "projects": 0, "experience": 0}}
    except Exception:
        data = {"name": None, "email": None, "department": None, "scores": {"cgpa": 0, "projects": 0, "experience": 0}}

    return data



def compute_weighted_score(scores):
    total = sum(WEIGHTS[k] * scores.get(k, 0) for k in WEIGHTS)
    return round(total, 2)

def handle_resume_screening():
    job_description = input("\nEnter the job role or description: ")

    resumes_dir = "Knowledge/resumes"
    results = []

    for file in os.listdir(resumes_dir):
        if not file.endswith(".txt"):
            continue

        with open(os.path.join(resumes_dir, file), "r", encoding="utf-8") as f:
            resume_text = f.read()

        data = evaluate_resume(resume_text, job_description)
        scores = data.get("scores", {})
        weighted = compute_weighted_score(scores)

        results.append({
            "candidate": data.get("name") or file.replace(".txt", "").title(),
            "email": data.get("email"),
            "department": data.get("department"),
            "scores": scores,
            "weighted": weighted
        })

    os.makedirs("Knowledge", exist_ok=True)
    with open("Knowledge/screening_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n✅ Screening results saved")
