from rich.console import Console
from rich.table import Table
from rich.spinner import Spinner
from rich import print as rprint

console = Console()


def print_error(message: str):
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str):
    console.print(f"[green]✓[/green] {message}")


def print_profiles_table(data: list):
    if not data:
        console.print("[yellow]No profiles found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", style="white")
    table.add_column("Gender", style="cyan")
    table.add_column("Age", justify="right")
    table.add_column("Age Group")
    table.add_column("Country")

    for profile in data:
        table.add_row(
            profile.get("name", ""),
            profile.get("gender", ""),
            str(profile.get("age", "")),
            profile.get("age_group", ""),
            profile.get("country_id", ""),
        )

    console.print(table)


def print_profile_detail(profile: dict):
    table = Table(show_header=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    fields = [
        ("ID", "id"),
        ("Name", "name"),
        ("Gender", "gender"),
        ("Gender Probability", "gender_probability"),
        ("Age", "age"),
        ("Age Group", "age_group"),
        ("Country", "country_id"),
        ("Country Name", "country_name"),
        ("Country Probability", "country_probability"),
        ("Created At", "created_at"),
    ]

    for label, key in fields:
        table.add_row(label, str(profile.get(key, "")))

    console.print(table)


def print_pagination_info(data: dict):
    console.print(
        f"[dim]Page {data.get('page')} of {data.get('total_pages')} "
        f"— {data.get('total')} total results[/dim]"
    )
