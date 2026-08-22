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

PROD_BACKEND_URL = "https://repo-scrapper-backend.politebush-f4d88b8a.eastasia.azurecontainerapps.io"
DEFAULT_API_URL = os.getenv("REPO_SCRAPPER_API_URL", PROD_BACKEND_URL)


def direct_github_fallback(prompt: str, limit: int) -> dict:
    """Direct GitHub REST API fallback with English + Hinglish keyword cleaning."""
    query_lower = prompt.lower()
    
    stop_words = {
        "top", "best", "give", "me", "show", "find", "a", "an", "the", "with", "for", "in", "microservices", 
        "list", "high", "stars", "repos", "projects", "repositories", "code", "repo",
        "mujhe", "ke", "ka", "ki", "ko", "se", "sabse", "dikhao", "karo", "wale", "wala", "wali", 
        "chahiye", "badhiya", "ache", "achha", "dhund", "do", "hai", "kuch", "par", "mein", "ho"
    }
    
    tokens = re.findall(r'\b[\w\+\-]+\b', query_lower)
    
    clean_words = []
    detected_lang = None

    for token in tokens:
        if token.isdigit():
            continue
        if token in ("python", "py") and not detected_lang:
            detected_lang = "python"
            continue
        if token not in stop_words:
            clean_words.append(token)

    clean_query = " ".join(clean_words).strip() or "machine learning"
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
        # Timeout 30 seconds set kiya gaya hai for Container App cold start
        response = requests.get(
            api_endpoint, 
            params={"prompt": prompt, "limit": limit}, 
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return {
            "query_used": f"{data.get('query_used', prompt)} (Sort: {data.get('sort_by', 'stars')}) [Production Server]",
            "total_found": data.get("total_found", len(data.get("results", []))),
            "results": data.get("results", [])
        }
    except Exception as e:
        console.print(f"[dim yellow]⚠️ Backend server unreachable ({e}). Switching to Direct GitHub Fallback...[/dim yellow]\n")
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


def execute_search_flow(prompt: str, limit: int, base_url: str):
    """Executes the search, renders table and opens action menu."""
    with console.status(f"[bold cyan]AI Searching for '[bold yellow]{prompt}[/bold yellow]'...", spinner="dots"):
        data = fetch_repositories(prompt=prompt, limit=limit, base_url=base_url)

    if data and data.get("results"):
        show_header(data["query_used"], data["total_found"], len(data["results"]))
        show_results_table(data["results"])
        interactive_menu(data["results"])
    else:
        console.print("[red]No matching repositories found. Try another query.[/red]\n")


def interactive_prompt_loop(default_limit: int, base_url: str):
    """Activates when user runs 'repo-scrapper' directly without arguments."""
    console.print("\n[bold cyan]🚀 Welcome to Repo Scrapper AI CLI![/bold cyan]")
    console.print("[dim]Type your natural language search query below (or 'exit' to quit).\n[/dim]")

    while True:
        prompt = questionary.text(
            "Enter repository search prompt:",
            qmark="🔍"
        ).ask()

        if not prompt or prompt.strip().lower() in ["exit", "quit", "q"]:
            console.print("[yellow]Exiting Repo Scrapper. Happy coding! 👋[/yellow]")
            break

        limit_choice = questionary.select(
            "How many repositories to fetch?",
            choices=["3", "5", "10", "15"],
            default=str(default_limit)
        ).ask()

        if not limit_choice:
            break

        execute_search_flow(prompt.strip(), int(limit_choice), base_url)

        # Ask if user wants to search again
        search_again = questionary.confirm("Do you want to search for another repo?", default=True).ask()
        if not search_again:
            console.print("[cyan]Goodbye! 👋[/cyan]")
            break


def main():
    parser = argparse.ArgumentParser(
        prog="repo-scrapper",
        description="AI-powered GitHub repository search and scraping CLI tool."
    )
    # nargs='?' makes prompt argument completely optional
    parser.add_argument("prompt", nargs="?", type=str, default=None, help="Search query (Optional in interactive mode)")
    parser.add_argument("--limit", type=int, default=3, help="Result count limit (default: 3)")
    parser.add_argument("--url", type=str, default=DEFAULT_API_URL, help="Backend API Base URL")
    args = parser.parse_args()

    if args.prompt is None:
        # Activated when user types simply `repo-scrapper`
        interactive_prompt_loop(default_limit=args.limit, base_url=args.url)
    else:
        # Single-command direct execution mode
        execute_search_flow(prompt=args.prompt, limit=args.limit, base_url=args.url)


if __name__ == "__main__":
    main()