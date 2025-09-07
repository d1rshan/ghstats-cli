#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

API_URL = "https://api.github.com/graphql"
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

# COLORS = ["#151B23", "#033A16", "#196C2E", "#2EA043", "#56D364"] # GITHUB's
# COLORS = ["#1F1F1F", "#057A2E", "#30C563", "#56E879", "#8BFFAD"] # LOW CONTRAST
COLORS = ["#444444", "#10A34A", "#30C563", "#56E879", "#8BFFAD"] # HIGH CONTRAST

def fetch_contributions(username: str):
    if not TOKEN:
        print("❌ [bold red]Error:[/bold red] GITHUB_TOKEN not found.")
        print("Please create a .env file with GITHUB_TOKEN or export it as an environment variable.")
        sys.exit(1)

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
                weekday
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        response = requests.post(API_URL, json={"query": query, "variables": {"login": username}}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ [bold red]HTTP Error:[/bold red] {e}")
        sys.exit(1)

    data = response.json()
    if "errors" in data:
        print(f"❌ [bold red]GitHub API Error:[/bold red] {data['errors'][0]['message']}")
        sys.exit(1)

    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

def get_color_for_count(count: int) -> str:
    if count == 0:
        return COLORS[0]
    elif count < 5:
        return COLORS[1]
    elif count < 10:
        return COLORS[2]
    elif count < 20:
        return COLORS[3]
    else:
        return COLORS[4]

def calculate_stats(weeks: list):
    all_days = [day for week in weeks for day in week["contributionDays"]]
    total_contributions = sum(day["contributionCount"] for day in all_days)

    longest_streak = 0
    current_streak = 0
    is_active_today = False

    if all_days:
        last_day_date = datetime.fromisoformat(all_days[-1]['date']).date()
        
        today = datetime.now(timezone.utc).date()
        
        if last_day_date >= today - timedelta(days=1) and all_days[-1]["contributionCount"] > 0:
            is_active_today = True

    for day in all_days:
        if day["contributionCount"] > 0:
            current_streak += 1
        else:
            longest_streak = max(longest_streak, current_streak)
            current_streak = 0
    longest_streak = max(longest_streak, current_streak)

    active_streak = current_streak if is_active_today else 0

    return {
        "total": total_contributions,
        "longest_streak": longest_streak,
        "current_streak": active_streak,
    }


def display_heatmap(username: str, weeks: list, stats: dict):
    console = Console()
    
    title = f"GitHub Contributions for [bold cyan]{username}[/bold cyan]"
    stats_text = (
        f"[bold]{stats['total']:,}[/bold] contributions in the last year\n"
        f"Longest Streak: [bold green]{stats['longest_streak']} days[/bold green] 🔥\n"
        f"Current Streak: [bold green]{stats['current_streak']} days[/bold green] ✨"
    )
    
    month_labels = Text(" " * 4) 
    last_month = None
    for i, week in enumerate(weeks):
        first_day_date = datetime.fromisoformat(week["contributionDays"][0]["date"])
        month = first_day_date.strftime("%b")
        if last_month != month:
            if i > 1: 
                month_labels.append(f"{month: <10}") 
            else:
                 month_labels.append(f"{month}")
            last_month = month
            
    grid = Table.grid(expand=False)
    grid.add_column(style="bold")  
    for _ in range(len(weeks)):
        grid.add_column()

    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    
    grid_data = [[] for _ in range(7)]
    for week in weeks:
        for i, day in enumerate(week["contributionDays"]):
            grid_data[i].append(day["contributionCount"])

    for i, label in enumerate(day_labels):
        row_cells = [f"{label} "]
        for count in grid_data[i]:
            color = get_color_for_count(count)
            row_cells.append(Text("■ ", style=color)) 
        grid.add_row(*row_cells)

    legend = Text("Less ", style="white")
    for color in COLORS:
        legend.append("■ ", style=color)
    legend.append("More", style="white")

    content_group = Group(
        Align.center(stats_text),
        "", 
        month_labels,
        Align.center(grid, style="on #000000"),
        "", 
        Align.center(legend),
    )
    
    console.print(Panel(
        Align.center(content_group),
        title=title,
        border_style="blue",
        padding=(1, 2)
    ))

def main():
    parser = argparse.ArgumentParser(description="View a GitHub contributions heatmap in your terminal.")
    parser.add_argument("username", help="GitHub username to fetch the heatmap for.")
    args = parser.parse_args()

    console = Console()
    with console.status(f"[bold green]Fetching data for {args.username}...[/]"):
        weeks_data = fetch_contributions(args.username)
        stats = calculate_stats(weeks_data)
    
    display_heatmap(args.username, weeks_data, stats)

if __name__ == "__main__":
    main()