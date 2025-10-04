from local_scheduler import Scheduler
from scheduler_agent import schedule_task

def get_task_from_user():
    print("\n=== Add a New Task ===")
    name = input("Task Name: ")
    time_input = input("Task Time (YYYY-MM-DD or YYYY-MM-DD HH:MM, optional): ")
    duration = input("Task Duration in hours (press Enter for default 1): ")
    details = input("Task Details (optional): ")

    task = {"name": name}
    if time_input:
        task["time"] = time_input
    if duration:
        task["duration"] = duration
    if details:
        task["details"] = details
    return task

if __name__ == "__main__":
    while True:
        task = get_task_from_user()
        # Schedule locally + Google Calendar
        schedule_task(task)

        more = input("Add another task? (y/n): ").strip().lower()
        if more != 'y':
            break
