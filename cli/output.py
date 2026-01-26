"""Output helpers with optional Rich support."""

# Try to import Rich, fallback to plain text
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class Output:
    """Unified output interface with Rich fallback."""

    def __init__(self):
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def print(self, message: str, style: str = None):
        """Print a message, optionally styled."""
        if HAS_RICH:
            self.console.print(message)
        else:
            # Strip Rich markup for plain output
            plain = self._strip_markup(message)
            print(plain)

    def error(self, message: str):
        """Print an error message."""
        if HAS_RICH:
            self.console.print(f"[red]Error:[/red] {message}")
        else:
            print(f"Error: {message}")

    def success(self, message: str):
        """Print a success message."""
        if HAS_RICH:
            self.console.print(f"[green]✓[/green] {message}")
        else:
            print(f"OK: {message}")

    def warning(self, message: str):
        """Print a warning message."""
        if HAS_RICH:
            self.console.print(f"[yellow]Warning:[/yellow] {message}")
        else:
            print(f"Warning: {message}")

    def status(self, message: str):
        """Return a status context manager."""
        if HAS_RICH:
            return self.console.status(f"[bold blue]{message}")
        else:
            return PlainStatus(message)

    def table(self, title: str, columns: list, rows: list):
        """Print a table."""
        if HAS_RICH:
            table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")
            for col in columns:
                table.add_column(col.get('name', ''),
                               style=col.get('style', ''),
                               justify=col.get('justify', 'left'),
                               width=col.get('width'))
            for row in rows:
                table.add_row(*[str(c) for c in row])
            self.console.print(table)
        else:
            # Plain text table
            print(f"\n=== {title} ===\n")
            if not rows:
                print("(empty)")
                return

            # Calculate column widths
            headers = [c.get('name', '') for c in columns]
            widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(widths):
                        widths[i] = max(widths[i], len(self._strip_markup(str(cell))))

            # Print header
            header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
            print(header_line)
            print("-" * len(header_line))

            # Print rows
            for row in rows:
                cells = []
                for i, cell in enumerate(row):
                    plain = self._strip_markup(str(cell))
                    if i < len(widths):
                        cells.append(plain.ljust(widths[i]))
                    else:
                        cells.append(plain)
                print("  ".join(cells))
            print()

    def panel(self, content: str, title: str = None):
        """Print a panel/box."""
        if HAS_RICH:
            self.console.print(Panel(content, title=title, box=box.ROUNDED))
        else:
            print(f"\n{'=' * 50}")
            if title:
                print(f" {title}")
                print("-" * 50)
            # Strip markup
            for line in content.split('\n'):
                print(f" {self._strip_markup(line)}")
            print("=" * 50)

    def progress_download(self, description: str):
        """Return a progress context for downloads."""
        if HAS_RICH:
            return RichProgress(self.console, description)
        else:
            return PlainProgress(description)

    def _strip_markup(self, text: str) -> str:
        """Remove Rich markup tags from text."""
        import re
        # Remove [tag] and [/tag] patterns
        return re.sub(r'\[/?[^\]]+\]', '', text)


class PlainStatus:
    """Plain text status context manager."""
    def __init__(self, message: str):
        self.message = message

    def __enter__(self):
        print(f"{self.message}...", end=" ", flush=True)
        return self

    def __exit__(self, *args):
        print("done")

    def update(self, message: str):
        pass


class RichProgress:
    """Rich progress bar wrapper."""
    def __init__(self, console, description: str):
        self.console = console
        self.description = description
        self.progress = None
        self.task = None

    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )
        self.progress.__enter__()
        self.task = self.progress.add_task(self.description, total=100)
        return self

    def __exit__(self, *args):
        self.progress.__exit__(*args)

    def update(self, downloaded: int, total: int):
        if total > 0:
            self.progress.update(self.task, completed=int(downloaded / total * 100))


class PlainProgress:
    """Plain text progress indicator."""
    def __init__(self, description: str):
        self.description = description
        self.last_percent = -1

    def __enter__(self):
        print(f"{self.description}", end="", flush=True)
        return self

    def __exit__(self, *args):
        print(" done")

    def update(self, downloaded: int, total: int):
        if total > 0:
            percent = int(downloaded / total * 100)
            if percent != self.last_percent and percent % 10 == 0:
                print(f" {percent}%", end="", flush=True)
                self.last_percent = percent


# Global output instance
out = Output()
