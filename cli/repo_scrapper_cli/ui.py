from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict, Any

console = Console()

def display_header():
    console.print(
        Panel.fit(
            "[bold cyan]🚀 REPO SCRAPPER CLI[/bold cyan]\n"
            "[dim]Production-Grade Rule-Based Natural Search Engine[/dim]",
            border_style="magenta"
        )
    )

def render_results_table(results: List[Dict[str, Any]], query_used: str, sort_by: str):
    if not results:
        console.print("[yellow]No repositories found matching your query.[/yellow]")
        return

    table = Table(
        title=f"Results for: '{query_used}' (Sorted by: {sort_by})", 
        show_header=True, 
        header_style="bold green"
    )
    
    table.add_column("⭐ Stars", justify="right", style="yellow")
    table.add_column("Repository", style="bold cyan", no_wrap=True)
    table.add_column("Language", style="magenta")
    table.add_column("Forks", justify="right", style="dim")
    table.add_column("Description", style="white")

    for repo in results:
        desc = repo.get("description") or "No description"
        if len(desc) > 60:
            desc = desc[:57] + "..."

        table.add_row(
            str(repo.get("stars", 0)),
            repo.get("full_name", ""),
            repo.get("language", "Unknown"),
            str(repo.get("forks", 0)),
            desc
        )

    console.print(table)