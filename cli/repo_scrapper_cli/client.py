import requests
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def search_repos(self, prompt: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Calls backend /api/v1/search endpoint with user prompt.
        """
        endpoint = f"{self.base_url}/api/v1/search"
        params = {"prompt": prompt, "limit": limit}

        try:
            response = requests.get(endpoint, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\n[Error] Failed to connect to backend service: {e}")
            return None