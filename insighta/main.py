import os
import sys
import webbrowser
import click
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from .auth import (
    load_credentials,
    save_credentials,
    clear_credentials,
    get_valid_token,
    logout as auth_logout,
    BASE_URL,
)
from .api import (
    get_profiles,
    get_profile,
    search_profiles,
    create_profile,
    export_profiles,
    whoami as whoami_api,
)
from .display import (
    console,
    print_error,
    print_success,
    print_profiles_table,
    print_profile_detail,
    print_pagination_info,
)

import requests


@click.group()
def cli():
    """Insighta Labs — Profile Intelligence CLI"""
    pass


@cli.command()
def login():
    """Login with GitHub OAuth"""
    console.print("[bold]Opening GitHub login in your browser...[/bold]")
    console.print(f"Visit: [cyan]{BASE_URL}/auth/github?cli=true[/cyan]")
    console.print("")
    console.print("After logging in, paste your access token and refresh token below.")
    console.print("[dim](They appear in the JSON response after GitHub redirects.)[/dim]")
    console.print("")

    access_token = click.prompt("Access token")
    refresh_token = click.prompt("Refresh token")

    # Verify the token works
    with Live(Spinner("dots", text="Verifying..."), refresh_per_second=10):
        try:
            response = requests.get(
                f"{BASE_URL}/auth/whoami",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            data = response.json()
        except Exception as e:
            print_error(f"Could not connect to server: {e}")
            sys.exit(1)

    if data.get("status") != "success":
        print_error("Invalid token. Please try again.")
        sys.exit(1)

    user = data["data"]
    save_credentials(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "username": user["username"],
            "role": user["role"],
        }
    )

    print_success(f"Logged in as @{user['username']} ({user['role']})")


@cli.command()
def logout():
    """Logout and clear credentials"""
    creds = load_credentials()
    if not creds:
        print_error("Not logged in.")
        return

    auth_logout(creds.get("refresh_token", ""))
    clear_credentials()
    print_success("Logged out successfully.")


@cli.command()
def whoami():
    """Show current logged in user"""
    if not get_valid_token():
        print_error("Not logged in. Run: insighta login")
        return

    with Live(Spinner("dots", text="Fetching user info..."), refresh_per_second=10):
        data = whoami_api()

    if not data or data.get("status") != "success":
        print_error(data.get("message", "Failed to fetch user info"))
        return

    user = data["data"]
    console.print(f"[bold]Username:[/bold] @{user['username']}")
    console.print(f"[bold]Email:[/bold] {user.get('email') or 'Not set'}")
    console.print(f"[bold]Role:[/bold] {user['role']}")
    console.print(f"[bold]Member since:[/bold] {user['created_at']}")


@cli.group()
def profiles():
    """Manage profiles"""
    pass


@profiles.command("list")
@click.option("--gender", default=None, help="Filter by gender")
@click.option("--country", default=None, help="Filter by country ID")
@click.option("--age-group", default=None, help="Filter by age group")
@click.option("--min-age", default=None, type=int, help="Minimum age")
@click.option("--max-age", default=None, type=int, help="Maximum age")
@click.option(
    "--sort-by", default=None, help="Sort by: age, created_at, gender_probability"
)
@click.option("--order", default=None, help="Order: asc or desc")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--limit", default=10, type=int, help="Results per page")
def list_profiles(
    gender, country, age_group, min_age, max_age, sort_by, order, page, limit
):
    """List profiles with optional filters"""
    if not get_valid_token():
        print_error("Not logged in. Run: insighta login")
        return

    params = {"page": page, "limit": limit}
    if gender:
        params["gender"] = gender
    if country:
        params["country_id"] = country
    if age_group:
        params["age_group"] = age_group
    if min_age:
        params["min_age"] = min_age
    if max_age:
        params["max_age"] = max_age
    if sort_by:
        params["sort_by"] = sort_by
    if order:
        params["order"] = order

    with Live(Spinner("dots", text="Fetching profiles..."), refresh_per_second=10):
        data = get_profiles(params)

    if not data or data.get("status") != "success":
        print_error(data.get("message", "Failed to fetch profiles"))
        return

    print_profiles_table(data["data"])
    print_pagination_info(data)


@profiles.command("get")
@click.argument("profile_id")
def get_profile_cmd(profile_id):
    """Get a single profile by ID"""
    if not get_valid_token():
        print_error("Not logged in. Run: insighta login")
        return

    with Live(Spinner("dots", text="Fetching profile..."), refresh_per_second=10):
        data = get_profile(profile_id)

    if not data or data.get("status") != "success":
        print_error(data.get("message", "Profile not found"))
        return

    print_profile_detail(data["data"])


@profiles.command("search")
@click.argument("query")
@click.option("--page", default=1, type=int)
@click.option("--limit", default=10, type=int)
def search_cmd(query, page, limit):
    """Search profiles using natural language"""
    if not get_valid_token():
        print_error("Not logged in. Run: insighta login")
        return

    with Live(Spinner("dots", text="Searching..."), refresh_per_second=10):
        data = search_profiles(query, {"page": page, "limit": limit})

    if not data or data.get("status") != "success":
        print_error(data.get("message", "Search failed"))
        return

    print_profiles_table(data["data"])
    print_pagination_info(data)


@profiles.command("create")
@click.option("--name", required=True, help="Name to classify")
def create_cmd(name):
    """Create a new profile (admin only)"""
    if not get_valid_token():
        print_error("Not logged in. Run: insighta login")
        return

    with Live(Spinner("dots", text="Creating profile..."), refresh_per_second=10):
        data = create_profile(name)

    if not data or data.get("status") != "success":
        print_error(data.get("message", "Failed to create profile"))
        return

    print_success(f"Profile created!")
    print_profile_detail(data["data"])


@profiles.command("export")
@click.option("--format", "fmt", default="csv", help="Export format (csv)")
@click.option("--gender", default=None)
@click.option("--country", default=None)
@click.option("--age-group", default=None)
def export_cmd(fmt, gender, country, age_group):
    """Export profiles to CSV"""
    if not get_valid_token():
        print_error("Not logged in. Run: insighta login")
        return

    params = {}
    if gender:
        params["gender"] = gender
    if country:
        params["country_id"] = country
    if age_group:
        params["age_group"] = age_group

    with Live(Spinner("dots", text="Exporting..."), refresh_per_second=10):
        response = export_profiles(params)

    if not response or response.status_code != 200:
        print_error("Export failed")
        return

    # Save to current directory
    filename = f"profiles_export.csv"
    content_disposition = response.headers.get("Content-Disposition", "")
    if "filename=" in content_disposition:
        filename = content_disposition.split("filename=")[1].strip('"')

    with open(filename, "wb") as f:
        f.write(response.content)

    print_success(f"Exported to {filename}")


if __name__ == "__main__":
    cli()
