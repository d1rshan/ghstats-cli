import sys
import click
from rich.console import Console
from .config import get_effective_config, write_config, read_config, CONFIG_FILE
from .heatmap import fetch_contributions, calculate_stats, display_heatmap

console = Console()

@click.group(invoke_without_command=True, context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--user', 'username', default=None, help='Show heatmap for a specific GitHub user.')
@click.pass_context
def main(ctx, username):
    """
    ghstats — A sleek tool to show GitHub contribution heatmaps in your terminal.

    \b
    Examples:
      ghstats                Show heatmap for the configured user.
      ghstats --user torvalds  Show heatmap for a specific user.
      ghstats setup          Start interactive setup.
      ghstats config         Open the configuration file.
    """
    if ctx.invoked_subcommand is not None:
        return

    show_heatmap(username)


def show_heatmap(username=None):
    """Fetches and displays the contribution heatmap."""
    cfg = get_effective_config()
    
    chosen_username = username or cfg.get("username")
    chosen_token = cfg.get("token")
    colors = cfg.get("colors")
    symbol = cfg.get("symbol")

    if not chosen_username:
        console.print("[bold red]No username found.[/bold red]")
        console.print("Run [bold cyan]ghstats setup[/bold cyan] or provide a user with [bold cyan]--user <username>[/bold cyan].")
        sys.exit(1)
        
    if not chosen_token:
        console.print("[bold red]No GitHub token found.[/bold red]")
        console.print("Please run [bold cyan]ghstats setup[/bold cyan] to configure your token.")
        sys.exit(1)

    with console.status(f"[bold green]Fetching data for {chosen_username}...[/]"):
        try:
            weeks = fetch_contributions(chosen_username, chosen_token)
            stats = calculate_stats(weeks)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    display_heatmap(chosen_username, weeks, stats, colors, symbol)


@main.command()
def setup():
    """Interactively configure your default username and GitHub token."""
    console.print("[bold cyan]GitHub Stats Setup[/bold cyan]")
    console.print(f"This will save your configuration to [dim]{CONFIG_FILE}[/dim]\n")
    
    current_username = read_config().get("username", "")
    new_username = click.prompt("GitHub username", default=current_username or None)
    
    console.print("\n[yellow]You need a GitHub Personal Access Token (PAT).[/yellow]")
    console.print("Create one at: https://github.com/settings/tokens/new")
    
    new_token = click.prompt("\nGitHub PAT", hide_input=True)
    
    if not new_username.strip() or not new_token.strip():
        console.print("[bold red]Username and token cannot be empty![/bold red]")
        sys.exit(1)
    
    write_config(username=new_username.strip(), token=new_token.strip())
    console.print(f"\n[green]✓ Configuration saved![/green]")
    console.print(f"Run [bold cyan]ghstats[/bold cyan] to see your heatmap!")


@main.command()
def config():
    """Open the configuration file in your default editor."""
    ensure_config_exists()
    console.print(f"Opening config file: [dim]{CONFIG_FILE}[/dim]")
    click.launch(str(CONFIG_FILE), locate=True)


@main.command("show-config")
def show_config():
    """Show current configuration with a masked token."""
    cfg = read_config()
    token = cfg.get("token", "")
    
    if token:
        masked_token = token[:4] + "..." + token[-4:] if len(token) > 8 else "****"
    else:
        masked_token = "[red]Not configured[/red]"
    
    console.print("\n[bold cyan]Current Configuration[/bold cyan]")
    console.print(f"Username : [bold]{cfg.get('username') or '[red]Not configured[/red]'}[/bold]")
    console.print(f"Token    : {masked_token}")
    console.print(f"\nConfig file location: [dim]{CONFIG_FILE}[/dim]")

def ensure_config_exists():
    """Helper to create config file if it doesn't exist."""
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        write_config()

if __name__ == "__main__":
    main()