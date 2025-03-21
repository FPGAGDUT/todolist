import unittest
from src.ai.client import AIClient
from src.ai.summarizer import Summarizer
from src.ai.suggestions import Suggestions

class TestAI(unittest.TestCase):

    def setUp(self):
        self.ai_client = AIClient()
        self.summarizer = Summarizer(self.ai_client)
        self.suggestions = Suggestions(self.ai_client)

    def test_summarizer(self):
        # Test summarizing functionality
        test_data = ["Task 1 completed", "Task 2 in progress", "Task 3 not started"]
        summary = self.summarizer.summarize(test_data)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

    def test_suggestions(self):
        # Test suggestions functionality
        test_todos = ["Finish report", "Prepare presentation", "Email client"]
        suggestion = self.suggestions.get_suggestions(test_todos)
        self.assertIsInstance(suggestion, list)
        self.assertGreater(len(suggestion), 0)

if __name__ == '__main__':
    unittest.main()