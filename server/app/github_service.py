import asyncio
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings


class GitHubScraperService:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Repo-Scrapper-Agent",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    async def _request(self, endpoint: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/{endpoint}", headers=self.headers, timeout=15.0)
            if response.status_code == 404:
                raise ValueError("Repository or resource not found on GitHub.")
            if response.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded. Please configure GITHUB_TOKEN.")
            response.raise_for_status()
            return response.json()

    async def get_repo_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        data = await self._request(f"repos/{owner}/{repo}")
        return {
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "default_branch": data.get("default_branch", "main"),
            "language": data.get("language"),
        }

    async def get_repo_tree(self, owner: str, repo: str, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        if not branch:
            meta = await self.get_repo_metadata(owner, repo)
            branch = meta["default_branch"]

        tree_data = await self._request(f"repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        
        filtered_tree = []
        for item in tree_data.get("tree", []):
            path = item.get("path", "")
            if not any(path.startswith(ignore) or f"/{ignore}/" in f"/{path}" for ignore in [".git", "node_modules", "__pycache__", ".venv"]):
                filtered_tree.append({
                    "path": item.get("path"),
                    "type": item.get("type"),
                    "size": item.get("size", 0),
                })
        return filtered_tree

    async def get_file_content(self, owner: str, repo: str, path: str, branch: str = "main") -> str:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(raw_url, headers=self.headers, timeout=10.0)
            if response.status_code == 404:
                raise ValueError(f"File '{path}' not found.")
            response.raise_for_status()
            return response.text

    async def fetch_files_batch(self, owner: str, repo: str, paths: List[str], branch: str = "main") -> Dict[str, str]:
        """Fetch raw content for multiple files concurrently."""
        async def _fetch(path: str):
            try:
                content = await self.get_file_content(owner, repo, path, branch)
                return path, content
            except Exception:
                return path, None

        tasks = [_fetch(path) for path in paths]
        results = await asyncio.gather(*tasks)
        return {path: content for path, content in results if content is not None}


github_service = GitHubScraperService()