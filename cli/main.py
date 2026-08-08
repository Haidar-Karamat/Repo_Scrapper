import argparse
import requests
import questionary
from repo_scrapper_cli.client import RepoScrapperClient
from repo_scrapper_cli.ui import (
    console,
    show_header,
    show_results_table,
    show_connection_error,
    show_error,
)
from repo_scrapper_cli.executor import (
    clone_repository,
    fork_repository,
    open_in_ide,
)


def interactive_menu(results: list):
    """Presents an interactive menu to clone, fork, or open selected repository in IDE."""
    if not results:
        return

    # 1. Format list options for questionary
    choices = [
        f"[{i+1}] {repo.get('full_name', repo.get('name', 'Unknown'))} (⭐ {repo.get('stars', 0):,})"
        for i, repo in enumerate(results)
    ]
    choices.append("❌ Exit")

    selected_choice = questionary.select(
        "Select a repository to perform action:",
        choices=choices
    ).ask()

    if not selected_choice or selected_choice == "❌ Exit":
        return

    # 2. Extract selected repo index & data
    idx = int(selected_choice.split("]")[0].replace("[", "")) - 1
    selected_repo = results[idx]
    full_name = selected_repo.get("full_name", selected_repo.get("name"))
    clone_url = selected_repo.get("clone_url")

    # 3. Prompt for specific action
    action = questionary.select(
        f"What would you like to do with '{full_name}'?",
        choices=[
            "📥 Clone to current directory",
            "🍴 Fork to my GitHub account",
            "💻 Clone & Open in VS Code",
            "❌ Exit"
        ]
    ).ask()

    # 4. Trigger executor functions
    if action == "📥 Clone to current directory":
        clone_repository(clone_url)
    elif action == "🍴 Fork to my GitHub account":
        fork_repository(full_name)
    elif action == "💻 Clone & Open in VS Code":
        if clone_repository(clone_url):
            open_in_ide(full_name)


def main():
    parser = argparse.ArgumentParser(description="Repo Scrapper Rich CLI Client")
    parser.add_argument("prompt", type=str, help="Search query (e.g., 'fastapi', 'llm', 'react')")
    parser.add_argument("--limit", type=int, default=3, help="Number of results to return (default: 3)")
    parser.add_argument("--sort", type=str, default="stars", help="Sort strategy (stars/forks)")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base API URL")

    args = parser.parse_args()
    client = RepoScrapperClient(base_url=args.url)

    with console.status(
        f"[bold cyan]Fetching repositories for '[bold yellow]{args.prompt}[/bold yellow]'...",
        spinner="dots",
    ):
        try:
            data = client.search_repositories(
                prompt=args.prompt, limit=args.limit, sort_by=args.sort
            )
        except requests.exceptions.ConnectionError:
            show_connection_error()
            return
        except requests.exceptions.HTTPError as err:
            show_error(f"HTTP Error: {err}")
            return
        except Exception as e:
            show_error(str(e))
            return

    if data:
        query_used = data.get("query_used", args.prompt)
        total_found = data.get("total_found", 0)
        results = data.get("results", [])

        # Display rich table UI
        show_header(query_used, total_found, len(results))
        show_results_table(results)

        # Trigger interactive clone/fork menu
        interactive_menu(results)


if __name__ == "__main__":
    main()