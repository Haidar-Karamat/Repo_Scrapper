import os
import subprocess
from rich.console import Console

console = Console()


def clone_repository(clone_url: str, target_dir: str = None) -> bool:
    """Clones the repository locally using git."""
    try:
        cmd = ["git", "clone", clone_url]
        if target_dir:
            cmd.append(target_dir)

        console.print(f"\n[bold cyan]📦 Cloning repository from {clone_url}...[/bold cyan]")
        result = subprocess.run(cmd, check=True, text=True)

        if result.returncode == 0:
            console.print("[bold green]✅ Repository cloned successfully![/bold green]")
            return True
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Git clone failed:[/bold red] {e}")
    except FileNotFoundError:
        console.print("[bold red]❌ Git is not installed or not in PATH.[/bold red]")
    return False


def fork_repository(full_name: str) -> bool:
    """Forks repository using GitHub CLI (gh)."""
    try:
        console.print(f"\n[bold cyan]🍴 Forking {full_name} to your GitHub account...[/bold cyan]")
        cmd = ["gh", "repo", "fork", full_name, "--clone=false"]
        result = subprocess.run(cmd, check=True, text=True)

        if result.returncode == 0:
            console.print("[bold green]✅ Repository forked successfully![/bold green]")
            return True
    except FileNotFoundError:
        console.print("[bold yellow]💡 GitHub CLI (gh) not found. Installing/authenticating 'gh' is required for auto-fork.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]❌ Fork failed:[/bold red] {e}")
    return False


def open_in_ide(repo_name: str, ide_cmd: str = "code"):
    """Opens cloned repo in VS Code or specified IDE."""
    repo_folder = repo_name.split("/")[-1]
    if os.path.exists(repo_folder):
        try:
            subprocess.run([ide_cmd, repo_folder], shell=True)
            console.print(f"[bold green]💻 Opened '{repo_folder}' in {ide_cmd.upper()}![/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Could not launch IDE:[/bold red] {e}")
    else:
        console.print(f"[bold yellow]⚠️ Folder '{repo_folder}' not found. Clone it first![/bold yellow]")