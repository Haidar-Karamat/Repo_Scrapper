
import os
import requests
from typing import List, Dict, Any

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "repo-scrapper-backend"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def search_repositories(self, query: str, sort: str = "stars", limit: int = 10) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": "desc",
            "per_page": limit
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            
            # Map GitHub API fields directly to what Pydantic model expects
            formatted_repos = []
            for item in items:
                owner_val = item.get("owner", {})
                owner_name = owner_val.get("login", "") if isinstance(owner_val, dict) else str(owner_val)
                
                formatted_repos.append({
                    "name": item.get("name", ""),
                    "full_name": item.get("full_name", ""),
                    "description": item.get("description") or "No description provided.",
                    "html_url": item.get("html_url", ""),
                    "clone_url": item.get("clone_url") or f"{item.get('html_url', '')}.git",
                    "owner": owner_name,
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language") or "N/A",
                    "default_branch": item.get("default_branch", "main"),
                    "topics": item.get("topics", [])
                })
            return formatted_repos
        except Exception as e:
            print(f"GitHub search error: {e}")
            return []