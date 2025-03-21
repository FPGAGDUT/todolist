from datetime import datetime, timedelta
import json

class Summarizer:
    def __init__(self, todo_data):
        self.todo_data = todo_data

    def generate_summary(self, days=7):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        summary = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
            "tasks": []
        }

        for task in self.todo_data:
            task_date = datetime.strptime(task['date'], '%Y-%m-%d')
            if start_date <= task_date <= end_date:
                summary["total_tasks"] += 1
                if task['status'] == 'completed':
                    summary["completed_tasks"] += 1
                else:
                    summary["pending_tasks"] += 1
                summary["tasks"].append(task)

        return json.dumps(summary, ensure_ascii=False, indent=4)

# Example usage:
# todo_data = [
#     {"title": "Task 1", "date": "2023-10-01", "status": "completed"},
#     {"title": "Task 2", "date": "2023-10-05", "status": "pending"},
#     {"title": "Task 3", "date": "2023-10-10", "status": "completed"},
# ]
# summarizer = Summarizer(todo_data)
# print(summarizer.generate_summary(days=10))