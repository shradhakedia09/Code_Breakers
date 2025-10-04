from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def handle_policy_question(question):
    with open("Knowledge/policy.txt", "r", encoding="utf-8") as f:
        policy_text = f.read()

    prompt = f"""
    You are an HR assistant. Use ONLY the following HR policy to answer the question.
    If the words confidential, secret, do not disclose, or any similar terms used to imply the fact that the data is reserved for for people higher in the company on must not be disclosed via such queries or requires prior permission from authorities then say, "I cannot give this information as it is against the company guidelines"

    POLICY:
    {policy_text}

    QUESTION:
    {question}

    If the answer is not found, reply: "I don’t see that in the HR policy. Please go through the policy"
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return resp.choices[0].message.content
    print("\nAnswer:", ask_policy(user_q))
