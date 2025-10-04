import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


with open("policy.txt", "r", encoding="utf-8") as f:
    policy_text = f.read()

def ask_policy(question: str):
    """
    Ask a question about the policy document.
    The model will answer only based on the text provided.
    """
    prompt = f"""
    You are a helpful policy assistant.
    Answer the question *only* using the following policy text.
    If the answer is not in the policy, say "I don't see that in the policy."

    POLICY:
    {policy_text}

    QUESTION:
    {question}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    answer = response.choices[0].message.content
    return answer


if __name__ == "__main__":
    print("🧠 Policy Assistant Ready! Type 'exit' to quit.")
    while True:
        user_q = input("\nWhat questions for you have regarding policy: ")
        if user_q.lower() in ["exit", "quit"]:
            break
        print("\nAnswer:", ask_policy(user_q))