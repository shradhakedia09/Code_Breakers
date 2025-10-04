import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



f = open("policy.txt", "r")
policy_text = f.read()
f.close()


def ask_policy(question: str):
    prompt = f"""
    You are a policy assistant for our company HR management software.
    Answer the question *only* using the following policy text.
    If the answer is not in the policy, say "I am unable to find this information currently. Please access the company policy"
    If there is any information regarding confidential information, sensitive information dangerous or top secret then do not display it say"I cannot give this informtion as it is against company guidelines".  POLICY:{policy_text} QUESTION:{question}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", 
                   "content": prompt}],
        temperature=0
    )

    answer = response.choices[0].message.content
    return answer


print("Policy Assistant Ready! Type 'exit' to quit.")
while True:
    user_q = input("\nWhat questions for you have regarding policy: ")
    if user_q.lower() in ["exit"]:
        break
    print("\nAnswer:", ask_policy(user_q))
