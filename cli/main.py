import sys
import questionary
from rich.console import Console
from repo_scrapper_cli.client import APIClient
from repo_scrapper_cli.ui import display_header, render_results_table

console = Console()

def main():
    display_header()
    client = APIClient(base_url="http://127.0.0.1:8000")

    while True:
        prompt = questionary.text(
            "Enter search query (e.g. 'top python fast api repos') or 'exit':"
        ).ask()

        if not prompt or prompt.strip().lower() == "exit":
            console.print("\n[bold green]Goodbye! 👋[/bold green]")
            sys.exit(0)

        limit_str = questionary.text(
            "How many repositories to display? [1-50]:",
            default="10"
        ).ask()

        try:
            limit = int(limit_str)
        except ValueError:
            limit = 10

        # Rich Status Spinner during API call
        with console.status("[bold green]Searching GitHub via Backend API...", spinner="dots"):
            response = client.search_repos(prompt=prompt, limit=limit)

        if response:
            render_results_table(
                results=response.get("results", []),
                query_used=response.get("query_used", prompt),
                sort_by=response.get("sort_by", "best-match")
            )
        else:
            console.print("[bold red]❌ Failed to fetch results. Ensure backend is running![/bold red]")

        console.print("\n" + "─" * 60 + "\n")

if __name__ == "__main__":
    main()