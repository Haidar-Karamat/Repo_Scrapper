import os
import requests
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor


class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "repo-scrapper-backend"
        })
        if self.token and not self.token.startswith("your_"):
            self.session.headers.update({"Authorization": f"token {self.token}"})

    def _fetch_repo_languages(self, owner: str, repo: str, default_lang: str) -> List[str]:
        """Fetch all programming languages used in the repository (sorted by usage)."""
        if not owner or not repo:
            return [default_lang] if default_lang and default_lang != "N/A" else ["N/A"]

        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            response = self.session.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Sort languages by bytes of code descending and take top 3
                    sorted_langs = sorted(data.items(), key=lambda x: x[1], reverse=True)
                    return [lang[0] for lang in sorted_langs[:3]]
        except Exception:
            pass

        return [default_lang] if default_lang and default_lang != "N/A" else ["N/A"]

    def search_repositories(self, query: str, sort: str = "stars", limit: int = 10) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": "desc",
            "per_page": limit
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            # Parallel language fetching for all returned repositories
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for item in items:
                    owner_val = item.get("owner", {})
                    owner_name = owner_val.get("login", "") if isinstance(owner_val, dict) else str(owner_val)
                    repo_name = item.get("name", "")
                    fallback_lang = item.get("language") or "N/A"
                    
                    futures.append(
                        executor.submit(self._fetch_repo_languages, owner_name, repo_name, fallback_lang)
                    )

                languages_results = [f.result() for f in futures]

            formatted_repos = []
            for idx, item in enumerate(items):
                owner_val = item.get("owner", {})
                owner_name = owner_val.get("login", "") if isinstance(owner_val, dict) else str(owner_val)
                repo_langs = languages_results[idx]
                primary_lang = repo_langs[0] if repo_langs else (item.get("language") or "N/A")

                formatted_repos.append({
                    "name": item.get("name", ""),
                    "full_name": item.get("full_name", ""),
                    "description": item.get("description") or "No description provided.",
                    "html_url": item.get("html_url", ""),
                    "clone_url": item.get("clone_url") or f"{item.get('html_url', '')}.git",
                    "owner": owner_name,
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "language": primary_lang,
                    "languages": repo_langs,
                    "default_branch": item.get("default_branch", "main"),
                    "topics": item.get("topics", [])
                })
            return formatted_repos
        except Exception as e:
            print(f"GitHub search failed: {e}")
            return []