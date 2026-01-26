"""Main CLI entry point using Click and Rich."""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich import box

from curseforge import CurseForgeClient, Config

console = Console()


def get_client_and_config():
    """Initialize config and client."""
    config = Config()

    if not config.api_key:
        console.print("[red]Error:[/red] API key not set. Run: hytale-cf config --api-key YOUR_KEY")
        raise SystemExit(1)

    client = CurseForgeClient(config.api_key)

    with console.status("[bold blue]Connecting to CurseForge..."):
        if not client.init_connection():
            console.print("[red]Error:[/red] Failed to connect to CurseForge API")
            raise SystemExit(1)

    return client, config


@click.group()
@click.version_option(version="1.0.0", prog_name="hytale-cf")
def main():
    """
    Hytale CurseForge CLI - APT-style mod manager.

    \b
    Examples:
        hytale-cf search magic        Search for mods containing "magic"
        hytale-cf install 12345       Install mod with ID 12345
        hytale-cf list                Show installed mods
        hytale-cf remove 12345        Remove mod with ID 12345
    """
    pass


@main.command()
@click.argument('query')
@click.option('-c', '--category', default='mods',
              type=click.Choice(['mods', 'worlds', 'prefabs', 'bootstrap', 'translations']),
              help='Category to search in')
@click.option('-n', '--limit', default=10, help='Number of results to show')
def search(query: str, category: str, limit: int):
    """Search for mods, worlds, or other resources."""
    client, config = get_client_and_config()

    with console.status(f"[bold blue]Searching for '{query}'..."):
        results, total = client.search(query, category=category, page_size=limit)

    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        return

    table = Table(
        title=f"Search Results ({len(results)}/{total})",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", width=8)
    table.add_column("Name", style="bold")
    table.add_column("Author", style="dim")
    table.add_column("Downloads", justify="right")
    table.add_column("Status", justify="center")

    for mod in results:
        mod_id = str(mod.get('id', ''))
        name = mod.get('name', 'Unknown')[:40]
        authors = mod.get('authors', [])
        author = authors[0]['name'] if authors else 'Unknown'
        downloads = f"{mod.get('downloadCount', 0):,}"

        # Check if installed
        status = "[green]✓[/green]" if config.is_installed(mod.get('id')) else ""

        table.add_row(mod_id, name, author, downloads, status)

    console.print(table)
    console.print("\n[dim]Use 'hytale-cf info <ID>' for details or 'hytale-cf install <ID>' to install[/dim]")


@main.command()
@click.argument('mod_id', type=int)
def info(mod_id: int):
    """Show detailed information about a mod."""
    client, config = get_client_and_config()

    with console.status("[bold blue]Fetching mod info..."):
        try:
            mod = client.get_mod(mod_id)
            files = client.get_files(mod_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return

    if not mod:
        console.print(f"[red]Mod {mod_id} not found[/red]")
        return

    # Build info panel
    authors = ", ".join(a['name'] for a in mod.get('authors', []))
    categories = ", ".join(c['name'] for c in mod.get('categories', []))
    latest_file = files[0] if files else {}

    info_text = Text()
    info_text.append(f"Name: ", style="bold")
    info_text.append(f"{mod.get('name', 'Unknown')}\n")
    info_text.append(f"ID: ", style="bold")
    info_text.append(f"{mod_id}\n")
    info_text.append(f"Authors: ", style="bold")
    info_text.append(f"{authors}\n")
    info_text.append(f"Categories: ", style="bold")
    info_text.append(f"{categories}\n")
    info_text.append(f"Downloads: ", style="bold")
    info_text.append(f"{mod.get('downloadCount', 0):,}\n")
    info_text.append(f"Latest Version: ", style="bold")
    info_text.append(f"{latest_file.get('displayName', 'N/A')}\n")
    info_text.append(f"File Size: ", style="bold")
    info_text.append(f"{latest_file.get('fileLength', 0) / 1024 / 1024:.2f} MB\n")

    installed = config.is_installed(mod_id)
    info_text.append(f"Installed: ", style="bold")
    info_text.append("Yes ✓\n" if installed else "No\n", style="green" if installed else "dim")

    if mod.get('summary'):
        info_text.append(f"\nSummary: ", style="bold")
        info_text.append(mod.get('summary', '')[:200])

    panel = Panel(info_text, title=f"[bold]{mod.get('name', 'Mod Info')}[/bold]", box=box.ROUNDED)
    console.print(panel)

    # Show links
    if mod.get('links', {}).get('websiteUrl'):
        console.print(f"\n[dim]Website:[/dim] {mod['links']['websiteUrl']}")


@main.command()
@click.argument('mod_id', type=int)
@click.option('-y', '--yes', is_flag=True, help='Skip confirmation')
def install(mod_id: int, yes: bool):
    """Install a mod by its ID."""
    client, config = get_client_and_config()

    if not config.game_path:
        console.print("[red]Error:[/red] Game path not set. Run: hytale-cf config --game-path /path/to/hytale")
        return

    # Check if already installed
    if config.is_installed(mod_id):
        console.print(f"[yellow]Mod {mod_id} is already installed[/yellow]")
        if not yes and not click.confirm("Reinstall?"):
            return

    # Get mod info first
    with console.status("[bold blue]Fetching mod info..."):
        try:
            mod = client.get_mod(mod_id)
            latest = client.get_latest_file(mod_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return

    mod_name = mod.get('name', f'Mod {mod_id}')
    file_name = latest.get('fileName', 'unknown')
    file_size = latest.get('fileLength', 0) / 1024 / 1024

    console.print(f"\n[bold]Package:[/bold] {mod_name}")
    console.print(f"[bold]File:[/bold] {file_name} ({file_size:.2f} MB)")

    if not yes and not click.confirm("\nProceed with installation?"):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # Download and install
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Installing {mod_name}...", total=100)

        def update_progress(downloaded, total):
            if total > 0:
                progress.update(task, completed=int(downloaded / total * 100))

        try:
            result = client.install_mod(mod_id, config.game_path, update_progress)
            config.add_installed(mod_id, result)
            progress.update(task, completed=100)
        except Exception as e:
            console.print(f"\n[red]Installation failed:[/red] {e}")
            return

    console.print(f"\n[green]✓[/green] Successfully installed [bold]{mod_name}[/bold]")
    console.print(f"[dim]Location: {result['path']}[/dim]")


@main.command()
@click.argument('mod_id', type=int)
@click.option('-y', '--yes', is_flag=True, help='Skip confirmation')
def remove(mod_id: int, yes: bool):
    """Remove an installed mod."""
    client, config = get_client_and_config()

    if not config.game_path:
        console.print("[red]Error:[/red] Game path not set.")
        return

    if not config.is_installed(mod_id):
        console.print(f"[yellow]Mod {mod_id} is not installed[/yellow]")
        return

    mod_info = config.installed_mods.get(str(mod_id), {})
    mod_name = mod_info.get('name', f'Mod {mod_id}')

    if not yes and not click.confirm(f"Remove {mod_name}?"):
        console.print("[yellow]Aborted.[/yellow]")
        return

    with console.status(f"[bold red]Removing {mod_name}..."):
        try:
            # Re-init client (we need it for uninstall)
            client, _ = get_client_and_config()
            success = client.uninstall_mod(mod_info, config.game_path)
            if success:
                config.remove_installed(mod_id)
                console.print(f"[green]✓[/green] Removed [bold]{mod_name}[/bold]")
            else:
                console.print(f"[yellow]Warning:[/yellow] File not found, removing from tracking")
                config.remove_installed(mod_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


@main.command('list')
@click.option('-v', '--verbose', is_flag=True, help='Show detailed info')
def list_installed(verbose: bool):
    """List all installed mods."""
    config = Config()

    installed = config.installed_mods
    if not installed:
        console.print("[dim]No mods installed.[/dim]")
        console.print("[dim]Use 'hytale-cf search <query>' to find mods[/dim]")
        return

    table = Table(
        title=f"Installed Mods ({len(installed)})",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold green",
    )
    table.add_column("ID", style="dim", width=8)
    table.add_column("Name", style="bold")
    table.add_column("Version")
    if verbose:
        table.add_column("File")
        table.add_column("Path")

    for mod_id, info in installed.items():
        row = [
            mod_id,
            info.get('name', 'Unknown')[:35],
            info.get('version', 'N/A')[:20],
        ]
        if verbose:
            row.append(info.get('filename', 'N/A'))
            row.append(info.get('path', 'N/A')[:40])
        table.add_row(*row)

    console.print(table)


@main.command()
@click.option('-y', '--yes', is_flag=True, help='Skip confirmation')
def update(yes: bool):
    """Check for and install updates for all mods."""
    client, config = get_client_and_config()

    installed = config.installed_mods
    if not installed:
        console.print("[dim]No mods installed.[/dim]")
        return

    console.print(f"[bold]Checking {len(installed)} mods for updates...[/bold]\n")

    updates_available = []

    with console.status("[bold blue]Checking for updates...") as status:
        for mod_id, info in installed.items():
            status.update(f"[bold blue]Checking {info.get('name', mod_id)}...")
            try:
                latest = client.get_latest_file(int(mod_id))
                current_file_id = info.get('file_id')
                if latest.get('id') != current_file_id:
                    updates_available.append({
                        'mod_id': int(mod_id),
                        'name': info.get('name', mod_id),
                        'current': info.get('version', 'N/A'),
                        'new': latest.get('displayName', 'N/A'),
                    })
            except Exception:
                pass

    if not updates_available:
        console.print("[green]✓[/green] All mods are up to date!")
        return

    table = Table(title="Updates Available", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Current Version")
    table.add_column("New Version", style="green")

    for upd in updates_available:
        table.add_row(
            str(upd['mod_id']),
            upd['name'],
            upd['current'],
            upd['new'],
        )

    console.print(table)

    if not yes and not click.confirm(f"\nUpdate {len(updates_available)} mods?"):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # Install updates
    for upd in updates_available:
        console.print(f"\n[bold]Updating {upd['name']}...[/bold]")
        try:
            result = client.install_mod(upd['mod_id'], config.game_path)
            config.add_installed(upd['mod_id'], result)
            console.print(f"[green]✓[/green] Updated {upd['name']}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to update {upd['name']}: {e}")


@main.command()
@click.option('--api-key', help='Set CurseForge API key')
@click.option('--game-path', help='Set Hytale game directory')
@click.option('--show', is_flag=True, help='Show current configuration')
def config(api_key: str, game_path: str, show: bool):
    """Configure API key and game path."""
    cfg = Config()

    if show:
        console.print(Panel(
            f"[bold]API Key:[/bold] {'*' * 8 + cfg.api_key[-8:] if cfg.api_key else '[red]Not set[/red]'}\n"
            f"[bold]Game Path:[/bold] {cfg.game_path or '[red]Not set[/red]'}\n"
            f"[bold]Config File:[/bold] {cfg.config_path}",
            title="Current Configuration",
            box=box.ROUNDED,
        ))
        return

    if api_key:
        cfg.api_key = api_key
        console.print("[green]✓[/green] API key saved")

    if game_path:
        import os
        if os.path.isdir(game_path):
            cfg.game_path = game_path
            console.print(f"[green]✓[/green] Game path set to: {cfg.game_path}")
        else:
            console.print(f"[red]Error:[/red] Directory does not exist: {game_path}")
            return

    if not api_key and not game_path:
        console.print("[dim]Usage:[/dim]")
        console.print("  hytale-cf config --api-key YOUR_KEY")
        console.print("  hytale-cf config --game-path /path/to/hytale")
        console.print("  hytale-cf config --show")


if __name__ == '__main__':
    main()
