import os
import requests
from typing import List, Optional
from .models import RepoItem


class GitHubClient:
    BASE_URL = "https://api.github.com/search/repositories"

    def __init__(self, token: Optional[str] = None):
        # Env variable se automatic fallback agar argument na pass kiya ho
        self.token = token or os.getenv("GITHUB_TOKEN")

    def search_repositories(
        self, query: str, sort: str = "stars", limit: int = 10
    ) -> List[RepoItem]:
        """
        Executes search against GitHub REST API and parses response into RepoItem models.
        """
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Repo-Scrapper-App",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        params = {
            "q": query,
            "sort": sort,
            "per_page": min(limit, 100),  
        }

        try:
            response = requests.get(
                self.BASE_URL, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                owner_data = item.get("owner") or {}
                raw_language = item.get("language")
                languages_list = [raw_language] if raw_language else []
                repo = RepoItem(
                    name=item.get("name", ""),
                    full_name=item.get("full_name", ""),
                    owner=owner_data.get("login", "unknown"),
                    description=item.get("description") or "No description provided.",
                    stars=item.get("stargazers_count", 0),
                    forks=item.get("forks_count", 0),
                    languages=languages_list,
                    clone_url=item.get("clone_url", ""),
                    default_branch=item.get("default_branch", "main"),
                    topics=item.get("topics", []),
                )
                results.append(repo)

            return results

        except requests.exceptions.RequestException as e:
            print(f"[Error] GitHub API Request failed: {e}")
            return []