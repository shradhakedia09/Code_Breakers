import heapq
import json
import time
from datetime import datetime, timedelta
import itertools

class Scheduler:
    def __init__(self, storage_file="tasks.json"):
        self.storage_file = storage_file
        self.tasks = []
        self.counter = itertools.count()
        self.load_tasks()

    def add_task(self, task, service=None):
        """Add a task with conflict resolution, rescheduling, and Google Calendar sync"""
        while True:
            time_input = task['time'].strip() if task.get('time') else ""
            if len(time_input) <= 10:  # only date
                time_input += " 09:00"

            # Preprocess single-digit month/day
            try:
                parts = time_input.split()[0].split('-')
                year, month, day = parts[0], parts[1].zfill(2), parts[2].zfill(2)
                if len(time_input.split()) == 1:
                    time_input = f"{year}-{month}-{day} 09:00"
                else:
                    time_input = f"{year}-{month}-{day} {time_input.split()[1]}"
            except Exception:
                print("❌ Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM.")
                task['time'] = input("Enter task time: ")
                continue

            try:
                start_time = datetime.strptime(time_input, "%Y-%m-%d %H:%M")
            except Exception:
                print("❌ Invalid date/time format. Try again.")
                task['time'] = input("Enter task time: ")
                continue

            duration_input = task.get('duration', '1')
            duration = int(duration_input) if str(duration_input).isdigit() else 1
            end_time = start_time + timedelta(hours=duration)

            # Check past
            now = datetime.now()
            if start_time < now:
                print(f"❌ Task '{task['name']}' is in the past ({start_time.strftime('%Y-%m-%d %H:%M')}).")
                task['time'] = input("Enter task time: ")
                continue

            # Check conflicts
            conflict_tasks = []
            for _, _, existing_task in self.tasks:
                existing_start = datetime.strptime(existing_task['time'], "%Y-%m-%d %H:%M")
                existing_end = existing_start + timedelta(hours=int(existing_task.get('duration',1)))
                if (start_time < existing_end) and (end_time > existing_start):
                    conflict_tasks.append(existing_task)

            if conflict_tasks:
                print(f"⚠️ Task '{task['name']}' overlaps with existing tasks:")
                for t in conflict_tasks:
                    existing_start = datetime.strptime(t['time'], "%Y-%m-%d %H:%M")
                    existing_end = existing_start + timedelta(hours=int(t.get('duration',1)))
                    print(f" - {t['name']} ({existing_start.strftime('%Y-%m-%d %H:%M')} - {existing_end.strftime('%Y-%m-%d %H:%M')})")
                print("Options:\n1. Reschedule current\n2. Reschedule all existing\n3. Delete current\n4. Delete all existing")
                choice = input("Enter choice (1-4): ").strip()

                if choice == "1":
                    task['time'] = input("New time for current task (HH:MM or YYYY-MM-DD HH:MM): ")
                    task['duration'] = input("Duration in hours (Enter for default 1): ") or 1
                    continue

                elif choice == "2":
                    for existing_task in conflict_tasks:
                        old_event_id = existing_task.get('google_event_id')
                        existing_task['time'] = input(f"New time for existing task '{existing_task['name']}': ")
                        existing_task['duration'] = input("Duration in hours (Enter for default 1): ") or 1
                        # Update Google Calendar event if available
                        if service and old_event_id:
                            try:
                                start_dt = datetime.strptime(existing_task['time'], "%Y-%m-%d %H:%M")
                                end_dt = start_dt + timedelta(hours=int(existing_task['duration']))
                                event = {
                                    'summary': existing_task.get('name', 'Task'),
                                    'description': str(existing_task.get('details','')),
                                    'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
                                    'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
                                }
                                service.events().update(calendarId='primary', eventId=old_event_id, body=event).execute()
                                print(f"✅ Updated '{existing_task['name']}' on Google Calendar")
                            except:
                                print(f"⚠️ Failed to update Google Calendar for '{existing_task['name']}'")
                    self.save_tasks()
                    continue

                elif choice == "3":
                    print(f"❌ Current task '{task['name']}' deleted.")
                    return

                elif choice == "4":
                    for t in conflict_tasks:
                        old_event_id = t.get('google_event_id')
                        if service and old_event_id:
                            try:
                                service.events().delete(calendarId='primary', eventId=old_event_id).execute()
                            except:
                                pass
                    self.tasks = [(ts,c,t) for ts,c,t in self.tasks if t not in conflict_tasks]
                    self.save_tasks()
                    continue

                else:
                    print("❌ Invalid choice.")
                    continue

            # No conflicts, add task
            task['time'] = start_time.strftime("%Y-%m-%d %H:%M")
            task['duration'] = duration
            task['timestamp'] = start_time.timestamp()
            count = next(self.counter)
            heapq.heappush(self.tasks, (task['timestamp'], count, task))
            self.save_tasks()
            print(f"✅ Task scheduled: {task['name']} at {task['time']} for {duration} hour(s)")
            break

    def run(self):
        if not self.tasks:
            print("No tasks to run.")
            return

        print("Scheduler running... Press Ctrl+C to stop.\n")
        try:
            while self.tasks:
                now = time.time()
                task_time, _, task = self.tasks[0]
                wait_seconds = task_time - now

                if wait_seconds <= 0:
                    heapq.heappop(self.tasks)
                    self.execute(task)
                    self.save_tasks()
                else:
                    print(f"Next task '{task['name']}' in {int(wait_seconds)} seconds...", end="\r")
                    time.sleep(min(wait_seconds, 1))
        except KeyboardInterrupt:
            print("\nScheduler stopped by user.")

    def execute(self, task):
        print(f"\n=== Executing Task: {task['name']} ===")
        print(f"Start Time: {task['time']}")
        print(f"Duration: {task.get('duration',1)} hour(s)")
        print(f"Details: {task.get('details', 'No details')}\n")

    def save_tasks(self):
        all_tasks = [t[2] for t in self.tasks]
        with open(self.storage_file, "w") as f:
            json.dump(all_tasks, f, indent=4)

    def load_tasks(self):
        try:
            with open(self.storage_file, "r") as f:
                tasks = json.load(f)
                for task in tasks:
                    if 'time' not in task:
                        continue
                    timestamp = datetime.strptime(task['time'], "%Y-%m-%d %H:%M").timestamp()
                    task['timestamp'] = timestamp
                    count = next(self.counter)
                    heapq.heappush(self.tasks, (timestamp, count, task))
        except FileNotFoundError:
            self.tasks = []
