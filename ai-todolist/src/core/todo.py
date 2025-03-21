# File: /ai-todolist/ai-todolist/src/core/todo.py

class Todo:
    def __init__(self, id, title, description, completed, created_at):
        self.id = id
        self.title = title
        self.description = description
        self.completed = completed
        self.created_at = created_at

    def mark_completed(self):
        self.completed = True

    def __repr__(self):
        return f'Todo(id={self.id}, title={self.title}, completed={self.completed})'