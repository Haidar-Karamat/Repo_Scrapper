from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_header(query_used: str, total_found: int, count: int) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold green]Query Used:[/bold green] [italic]{query_used}[/italic]  │  "
            f"[bold green]Total Found:[/bold green] [bold yellow]{total_found:,}[/bold yellow]  │  "
            f"[bold green]Displaying Top:[/bold green] [bold cyan]{count}[/bold cyan]",
            title="[bold magenta]🚀 REPO SCRAPPER CLI[/bold magenta]",
            expand=False,
            border_style="magenta",
        )
    )


def show_results_table(results: List[Dict[str, Any]]) -> None:
    if not results:
        console.print("\n[yellow]No repositories found matching your query.[/yellow]")
        return

    table = Table(
        title="[dim]Search Results[/dim]",
        show_header=True,
        header_style="bold cyan",
        border_style="bright_blue",
        title_justify="left",
    )

    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Repository Name", style="bold bright_white", min_width=22)
    table.add_column("Stats", style="bold yellow", justify="center", width=14)
    table.add_column("Languages", style="bold green", width=14)
    table.add_column("Details & Topics", style="white")

    for idx, repo in enumerate(results, start=1):
        name = repo.get("full_name", repo.get("name", "Unknown"))
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        stats_str = f"⭐ {stars:,}\n🍴 {forks:,}"

        # ⚡ Language extraction fix: handles both single string & list
        lang_data = repo.get("language") or repo.get("languages")
        if isinstance(lang_data, list):
            langs = ", ".join([str(l) for l in lang_data if l]) or "N/A"
        elif isinstance(lang_data, str) and lang_data.strip():
            langs = lang_data.strip()
        else:
            langs = "N/A"

        desc = repo.get("description") or "No description provided."
        topics_list = repo.get("topics") or []
        topics_formatted = " ".join([f"[dim cyan]#{t}[/dim cyan]" for t in topics_list[:4]])

        clone_url = repo.get("clone_url", "")
        details_cell = f"{desc}\n{topics_formatted}\n[dim underline blue]{clone_url}[/dim underline blue]"

        table.add_row(str(idx), name, stats_str, langs, details_cell)

    console.print(table)


def show_connection_error(url: str = "http://localhost:8000"):
    console.print(f"\n[bold red]❌ Connection Error:[/bold red] Could not connect to API at [underline]{url}[/underline].")


def show_error(message: str):
    """Prints an error message in rich formatted style."""
    console.print(f"\n[bold red]❌ Error:[/bold red] {message}")