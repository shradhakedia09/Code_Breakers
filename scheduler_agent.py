from datetime import datetime, timedelta
import os
import socket
import pytz
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
from local_scheduler import Scheduler

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-4.1-mini"
SCOPES = ['https://www.googleapis.com/auth/calendar']

client = OpenAI(api_key=OPENAI_API_KEY)

def get_calendar_service():
    try:
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception:
        print("❌ Could not connect to Google Calendar. Check your internet or authentication.")
        return None

def get_free_slots(service, start_dt, end_dt, duration_hours=1):
    duration_minutes = duration_hours * 60
    if not service:
        return []

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
    except (HttpError, socket.gaierror):
        print("❌ Could not reach Google Calendar. Check your internet connection.")
        return []

    events = events_result.get('items', [])
    busy_times = []
    tz = pytz.timezone("Asia/Kolkata")
    for event in events:
        start = tz.localize(datetime.fromisoformat(event['start'].get('dateTime')))
        end = tz.localize(datetime.fromisoformat(event['end'].get('dateTime')))
        busy_times.append((start, end))

    free_slots = []
    current = start_dt
    while current + timedelta(minutes=duration_minutes) <= end_dt:
        slot_end = current + timedelta(minutes=duration_minutes)
        overlap = any(current < b_end and slot_end > b_start for b_start, b_end in busy_times)
        if not overlap:
            free_slots.append(current)
        current += timedelta(minutes=15)
    return free_slots

def suggest_time_with_llm(free_slots, task_details):
    if not free_slots:
        return None

    free_str = ", ".join([slot.strftime("%Y-%m-%d %H:%M") for slot in free_slots])
    prompt = f"I need to schedule a {task_details['name']} for {task_details.get('candidate','someone')}." \
             f" Available slots: {free_str}. Choose best {task_details.get('duration',1)}-hour slot." \
             f" Return YYYY-MM-DD HH:MM."
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role":"user","content":prompt}],
            max_tokens=20
        )
        suggested_time = response.choices[0].message.content.strip()
        tz = pytz.timezone("Asia/Kolkata")
        return tz.localize(datetime.strptime(suggested_time, "%Y-%m-%d %H:%M"))
    except Exception:
        return free_slots[0] if free_slots else None

def schedule_task(task):
    scheduler = Scheduler()
    service = get_calendar_service()
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    duration_hours = int(task.get('duration',1))
    task['duration'] = duration_hours

    if 'time' not in task or not task['time']:
        start_dt = now
        end_dt = start_dt + timedelta(days=7)
        free_slots = get_free_slots(service, start_dt, end_dt, duration_hours)
        chosen_time = suggest_time_with_llm(free_slots, task) if free_slots else start_dt
    else:
        time_input = task['time'].strip()
        if len(time_input) <= 10:
            time_input += " 09:00"
        try:
            chosen_time = tz.localize(datetime.strptime(time_input, "%Y-%m-%d %H:%M"))
        except Exception:
            print("❌ Invalid date/time format. Using current time locally.")
            chosen_time = now
    if chosen_time < now:
        chosen_time = now
    task['time'] = chosen_time.strftime("%Y-%m-%d %H:%M")

    # Add locally with service reference (for rescheduling on Google)
    scheduler.add_task(task, service=service)

    # Add to Google Calendar if not already added
    if service:
        try:
            end_time = chosen_time + timedelta(hours=duration_hours)
            event = {
                'summary': task.get('name', 'Task'),
                'description': str(task.get('details','')),
                'start': {'dateTime': chosen_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
            }
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            task['google_event_id'] = created_event['id']
            print(f"✅ Task scheduled on Google Calendar at {task['time']}")
            print(f"🔗 Open in calendar: {created_event.get('htmlLink')}")
        except (HttpError, socket.gaierror):
            print("❌ Could not add to Google Calendar. Check your internet connection.")
