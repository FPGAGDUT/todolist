import unittest
from src.desktop.app import TodoApp

class TestDesktopApp(unittest.TestCase):

    def setUp(self):
        self.app = TodoApp()

    def test_create_todo(self):
        self.app.create_todo("Test Todo")
        self.assertIn("Test Todo", self.app.todos)

    def test_complete_todo(self):
        self.app.create_todo("Test Todo")
        self.app.complete_todo("Test Todo")
        self.assertTrue(self.app.todos["Test Todo"].completed)

    def test_reminder_set(self):
        self.app.create_todo("Test Todo with Reminder", reminder_time="10:00")
        self.assertEqual(self.app.todos["Test Todo with Reminder"].reminder_time, "10:00")

    def test_summary(self):
        self.app.create_todo("Test Todo 1")
        self.app.create_todo("Test Todo 2")
        summary = self.app.get_summary()
        self.assertEqual(len(summary), 2)

if __name__ == '__main__':
    unittest.main()