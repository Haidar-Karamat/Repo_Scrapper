import os
import requests
from typing import List, Dict, Any

class GitHubClient:
    BASE_URL = "https://api.github.com/search/repositories"

    def __init__(self):
        token_candidate = os.getenv("GITHUB_TOKEN", "").strip()
        # Ensure it's not a placeholder
        if token_candidate and len(token_candidate) > 15 and not token_candidate.lower().startswith(("your_", "ghp_your_", "dummy")):
            self.token = token_candidate
        else:
            self.token = ""

    def search_repositories(self, query: str, sort: str = "stars", limit: int = 10) -> List[Dict[str, Any]]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "repo-scrapper-app"
        }

        # Send Authorization header ONLY if a valid token exists
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        params = {
            "q": query,
            "sort": sort,
            "order": "desc",
            "per_page": min(limit, 50)
        }

        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            results = []
            for item in items:
                results.append({
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "html_url": item.get("html_url"),
                    "description": item.get("description", ""),
                    "stargazers_count": item.get("stargazers_count", 0),
                    "forks_count": item.get("forks_count", 0),
                    "language": item.get("language")
                })
            return results

        except requests.exceptions.RequestException as e:
            print(f"[Error] GitHub API Request failed: {e}")
            return []