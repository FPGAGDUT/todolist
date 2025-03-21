import unittest
from src.core.todo import Todo
from src.core.project import Project

class TestCore(unittest.TestCase):

    def setUp(self):
        self.todo_item = Todo(title="Test Todo", description="This is a test todo item.")
        self.project = Project(name="Test Project")

    def test_todo_creation(self):
        self.assertEqual(self.todo_item.title, "Test Todo")
        self.assertEqual(self.todo_item.description, "This is a test todo item.")
        self.assertFalse(self.todo_item.completed)

    def test_todo_mark_completed(self):
        self.todo_item.mark_completed()
        self.assertTrue(self.todo_item.completed)

    def test_project_creation(self):
        self.assertEqual(self.project.name, "Test Project")
        self.assertEqual(len(self.project.todos), 0)

    def test_project_add_todo(self):
        self.project.add_todo(self.todo_item)
        self.assertEqual(len(self.project.todos), 1)
        self.assertEqual(self.project.todos[0].title, "Test Todo")

if __name__ == '__main__':
    unittest.main()