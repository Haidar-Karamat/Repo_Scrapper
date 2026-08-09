import argparse
import os
import webbrowser
import requests
import questionary
from dotenv import load_dotenv
import re

from repo_scrapper_cli.ui import console, show_header, show_results_table, show_error
from repo_scrapper_cli.executor import clone_repository, fork_repository, open_in_ide

load_dotenv()

DEFAULT_API_URL = os.getenv("REPO_SCRAPPER_API_URL", "http://localhost:8000")


def direct_github_fallback(prompt: str, limit: int) -> dict:
    """Direct GitHub REST API fallback with keyword cleaning."""
    query_lower = prompt.lower()
    
    # Stop-words aur digits filter karein taaki GitHub query clean bane
    stop_words = {"top", "best", "give", "me", "show", "find", "a", "an", "the", "with", "for", "in", "microservices"}
    tokens = re.findall(r'\b[\w\+\-]+\b', query_lower)
    
    clean_words = []
    detected_lang = None

    for token in tokens:
        if token.isdigit():
            continue  # "3" jaise numbers drop karein
        if token in ("python", "py") and not detected_lang:
            detected_lang = "python"
            continue
        if token not in stop_words:
            clean_words.append(token)

    clean_query = " ".join(clean_words).strip() or "microservice"
    if detected_lang:
        github_q = f"{clean_query} language:{detected_lang}"
    else:
        github_q = f"{clean_query} language:python"

    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token and token.strip() and not token.startswith("your_"):
        headers["Authorization"] = f"token {token.strip()}"

    url = f"https://api.github.com/search/repositories?q={github_q}&sort=stars&order=desc&per_page={limit}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 401 and "Authorization" in headers:
            del headers["Authorization"]
            response = requests.get(url, headers=headers, timeout=10)

        response.raise_for_status()
        raw_data = response.json()
    except Exception as e:
        show_error(f"GitHub Fallback Error: {e}")
        return None

    results = []
    for item in raw_data.get("items", []):
        results.append({
            "name": item.get("name"),
            "full_name": item.get("full_name"),
            "description": item.get("description") or "No description provided",
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "language": item.get("language") or "N/A",
            "topics": item.get("topics", [])[:5],
            "html_url": item.get("html_url"),
            "clone_url": item.get("clone_url") or f"{item.get('html_url')}.git",
        })

    return {
        "query_used": f"{github_q} [Local Fallback Mode]",
        "total_found": raw_data.get("total_count", len(results)),
        "results": results,
    }


def fetch_repositories(prompt: str, limit: int, base_url: str) -> dict:
    """Hybrid Fetcher: FastAPI Server -> Direct GitHub Fallback."""
    api_endpoint = f"{base_url.rstrip('/')}/api/v1/search"
    
    try:
        response = requests.get(api_endpoint, params={"prompt": prompt, "limit": limit}, timeout=6)
        response.raise_for_status()
        data = response.json()
        return {
            "query_used": f"{data['query_used']} (Sort: {data.get('sort_by', 'stars')})",
            "total_found": data.get("total_found", len(data.get("results", []))),
            "results": data.get("results", [])
        }
    except Exception:
        console.print("[dim yellow]⚠️ Backend server unreachable. Switching to Direct GitHub Fallback...[/dim yellow]\n")
        return direct_github_fallback(prompt, limit)


def interactive_menu(results: list):
    if not results:
        return

    choices = [
        f"[{i+1}] {repo.get('full_name', repo.get('name'))} (⭐ {repo.get('stars', 0):,})"
        for i, repo in enumerate(results)
    ]
    choices.append("❌ Exit")

    selected = questionary.select("Select a repository:", choices=choices).ask()
    if not selected or selected == "❌ Exit":
        return

    idx = int(selected.split("]")[0].replace("[", "")) - 1
    selected_repo = results[idx]
    full_name = selected_repo.get("full_name")
    clone_url = selected_repo.get("clone_url")
    html_url = selected_repo.get("html_url")

    action = questionary.select(
        f"Action for '{full_name}':",
        choices=[
            "📥 Clone to current directory",
            "🍴 Fork to my GitHub account",
            "💻 Clone & Open in VS Code",
            "🌐 Open in Web Browser",
            "❌ Exit"
        ]
    ).ask()

    if action == "📥 Clone to current directory":
        clone_repository(clone_url)
    elif action == "🍴 Fork to my GitHub account":
        fork_repository(full_name)
    elif action == "💻 Clone & Open in VS Code":
        if clone_repository(clone_url):
            open_in_ide(full_name)
    elif action == "🌐 Open in Web Browser":
        webbrowser.open(html_url)


def main():
    parser = argparse.ArgumentParser(description="Repo Scrapper Hybrid AI CLI")
    parser.add_argument("prompt", type=str, help="Search query")
    parser.add_argument("--limit", type=int, default=3, help="Result count limit")
    parser.add_argument("--url", type=str, default=DEFAULT_API_URL, help="Backend API Base URL")
    args = parser.parse_args()

    with console.status(f"[bold cyan]AI Searching for '[bold yellow]{args.prompt}[/bold yellow]'...", spinner="dots"):
        data = fetch_repositories(prompt=args.prompt, limit=args.limit, base_url=args.url)

    if data:
        show_header(data["query_used"], data["total_found"], len(data["results"]))
        show_results_table(data["results"])
        interactive_menu(data["results"])


if __name__ == "__main__":
    main()