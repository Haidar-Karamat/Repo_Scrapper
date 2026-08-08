import requests
from typing import Dict, Any, Optional
import os


class RepoScrapperClient:
    def __init__(self, base_url: str = None):
        default_url = os.getenv("REPO_SCRAPPER_API_URL", "http://localhost:8000")
        self.base_url = (base_url or default_url).rstrip("/")

    def search_repositories(
        self, prompt: str, limit: int = 3, sort_by: str = "stars"
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/search"
        params = {"prompt": prompt, "limit": limit, "sort_by": sort_by}

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()