import os
from Agents.policy_agent import handle_policy_question
from Agents.resume_agent import handle_resume_screening
from Agents.onboarding_agent import handle_onboarding


def route_query(user_input):
    text = user_input.lower()
    if "policy" in text or "leave" in text or "benefit" in text:
        return handle_policy_question(user_input)
    elif "resume" in text or "screen" in text or "candidate" in text:
        return handle_resume_screening()
    elif "onboard" in text or "joining" in text or "reporting" in text:
        return handle_onboarding()
    else:
        return "I can handle HR policy, resume screening, or onboarding requests."

if __name__ == "__main__":
    print("🤖 HR Multi-Agent Assistant ready!")
    while True:
        user_q = input("\nYou: ")
        if user_q.lower() in ["exit", "quit"]:
            break
        print("Assistant:", route_query(user_q))