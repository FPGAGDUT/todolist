# File: /ai-todolist/ai-todolist/src/core/database.py

import sqlite3

class Database:
    def __init__(self, db_name='todolist.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.connection.commit()

    def add_todo(self, title, description=''):
        self.cursor.execute('''
            INSERT INTO todos (title, description) VALUES (?, ?)
        ''', (title, description))
        self.connection.commit()

    def get_todos(self):
        self.cursor.execute('SELECT * FROM todos')
        return self.cursor.fetchall()

    def update_todo(self, todo_id, completed):
        self.cursor.execute('''
            UPDATE todos SET completed = ? WHERE id = ?
        ''', (completed, todo_id))
        self.connection.commit()

    def close(self):
        self.connection.close()

