import os
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables (for SMTP credentials)
load_dotenv()

# ============= Email Sending Helper =============
def send_email(recipient, subject, body):
    """Send an email via SMTP using credentials in .env."""
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    if not sender or not password:
        return "⚠️ Email credentials missing in .env file."

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        # Gmail SMTP (SSL)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        return f"✅ Email sent successfully to {recipient}."
    except Exception as e:
        return f"❌ Failed to send email: {e}"

# ============= Onboarding Handler =============
def handle_onboarding():
    candidate_name = input("Enter candidate name for onboarding: ").title()

    results_path = "Knowledge/screening_results.json"
    if not os.path.exists(results_path):
        return "⚠️ No screening results found. Please run resume screening first."

    # Load screening results
    with open(results_path, "r", encoding="utf-8") as f:
        screening_results = json.load(f)

    # Find candidate
    candidate_entry = next((r for r in screening_results if r["candidate"] == candidate_name), None)
    if not candidate_entry:
        return f"❌ Candidate '{candidate_name}' not found in screening results."

    # Enforce threshold (optional)
    if candidate_entry.get("weighted", 0) < 80:
        return f"⚠️ Candidate '{candidate_name}' scored {candidate_entry['weighted']} (below 80 threshold). Not approved for onboarding."

    # Retrieve details
    email = candidate_entry.get("email")
    department = candidate_entry.get("department") or "General Department"
    position = department or "New Hire"

    if not email:
        email = input(f"Enter email for {candidate_name}: ")

    # Generate onboarding details
    report_date = datetime.now() + timedelta(days=random.randint(3, 7))
    formatted_date = report_date.strftime("%A, %d %B %Y")
    reporting_time = "9:00 AM"

    # Load or use default template
    try:
        with open("Knowledge/onboarding_template.txt", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        template = (
            "Dear {name},\n\n"
            "Congratulations on joining {department} as a {position}!\n"
            "Your reporting date is {date} at {time}.\n\n"
            "Please bring all necessary documents and report to the HR desk upon arrival.\n\n"
            "Welcome aboard!\n\nBest,\nHR Team"
        )

    # Fill placeholders
    message = template.format(
        name=candidate_name,
        position=position,
        department=department,
        date=formatted_date,
        time=reporting_time
    )

    # Save onboarding letter locally
    save_dir = "Knowledge/onboarding_letters"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{candidate_name}_onboarding.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(message)

    print(f"✅ Onboarding letter saved: {file_path}")

    # Send email
    email_status = send_email(email, "Your Onboarding Details", message)
    return email_status
