class Project:
    def __init__(self, name, description, deadline=None):
        self.name = name
        self.description = description
        self.deadline = deadline
        self.todos = []

    def add_todo(self, todo):
        self.todos.append(todo)

    def remove_todo(self, todo):
        self.todos.remove(todo)

    def get_todos(self):
        return self.todos

    def __repr__(self):
        return f"Project(name={self.name}, description={self.description}, deadline={self.deadline}, todos={self.todos})"