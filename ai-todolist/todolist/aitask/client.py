import requests

class AIClient:
    def __init__(self, api_key, base_url="https://api.example.com"):
        self.api_key = api_key
        self.base_url = base_url

    def get_reminders(self):
        response = requests.get(f"{self.base_url}/reminders", headers=self._get_headers())
        return response.json()

    def summarize_activity(self, activities):
        response = requests.post(f"{self.base_url}/summarize", json={"activities": activities}, headers=self._get_headers())
        return response.json()

    def get_suggestions(self, todo_items):
        response = requests.post(f"{self.base_url}/suggestions", json={"todo_items": todo_items}, headers=self._get_headers())
        return response.json()

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }