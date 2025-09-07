#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from rich.console import Console, Group
from rich.panel import Panel
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from rich.align import Align

API_URL = "https://api.github.com/graphql"
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

# COLORS = ["#151B23", "#033A16", "#196C2E", "#2EA043", "#56D364"] # GITHUB's
COLORS = ["#151B23", "#057A2E", "#30C563", "#56E879", "#8BFFAD"] # LOW CONTRAST

SYMBOL = "■"
# SYMBOL = "⬤"
# SYMBOL = "◍"
# SYMBOL = "▮"
# SYMBOL = "◉"
# SYMBOL = "◆"
# SYMBOL = "▬"
# SYMBOL = "◘"
# SYMBOL = "▼"
# SYMBOL = "◩"
# SYMBOL = "◯"


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
    console = Console(force_terminal=True, color_system="truecolor")

    title = f"GitHub Contributions for [bold cyan]{username}[/bold cyan]"
    stats_text = (
        f"[bold]{stats['total']:,}[/bold] contributions in the last year\n"
        f"Longest Streak: [bold green]{stats['longest_streak']} days[/bold green] 🗿\n"
        f"Current Streak: [bold green]{stats['current_streak']} days[/bold green] 🔥"
    )


    cell_width = len(SYMBOL) + 1
    total_heatmap_width = len(weeks) * cell_width

    label_canvas = [' '] * total_heatmap_width
    last_month = None

    for i, week in enumerate(weeks):
        if not week["contributionDays"]:
            continue
        
        first_day_of_week = datetime.fromisoformat(week["contributionDays"][0]["date"])
        month_of_first_day = first_day_of_week.strftime("%b")

        if month_of_first_day != last_month:
            start_pos = i * cell_width
            month_str = month_of_first_day
            
            for j in range(len(month_str)):
                if start_pos + j < len(label_canvas):
                    label_canvas[start_pos + j] = month_str[j]
            
            last_month = month_of_first_day

    month_labels = Text(" " * 4) + Text("".join(label_canvas))

    labels_table = Table.grid(expand=False)
    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    for label in day_labels:
        labels_table.add_row(f"{label} ")

    heatmap_table = Table.grid(expand=False, padding=(0, 1)) 
    for _ in range(len(weeks)):
        heatmap_table.add_column()

    grid_data = [[] for _ in range(7)]
    for week in weeks:
        days_in_week = {day['weekday']: day['contributionCount'] for day in week['contributionDays']}
        for i in range(7):
            grid_data[i].append(days_in_week.get(i, 0))

    for i in range(7):
        row_cells = []
        for count in grid_data[i]:
            color = get_color_for_count(count)
            row_cells.append(Text(SYMBOL, style=color))
        heatmap_table.add_row(*row_cells)

    heatmap_with_bg = Padding(heatmap_table, (0, 1), style="on #000000")

    layout_table = Table.grid(expand=False, padding=0)
    layout_table.add_column(style="bold", justify="right")  
    layout_table.add_column()  
    layout_table.add_row(labels_table, Align.center(heatmap_with_bg))

    legend = Text("Less ", style="white")
    for color in COLORS:
        legend.append(SYMBOL + " ", style=color)
    legend.append("More", style="white")

    content_group = Group(
        Align.center(stats_text),
        "", 
        month_labels,
        layout_table,  
        "", 
        Align.center(legend),
    )

    console.print(
        Panel(
            Align.center(content_group),
            title=title,
            border_style="blue",
            padding=(1, 2),
        )
    )

def main():
    parser = argparse.ArgumentParser(description="View a GitHub contributions heatmap in your terminal.")
    parser.add_argument("username", help="GitHub username to fetch the heatmap for.")
    args = parser.parse_args()

    console = Console(force_terminal=True, color_system="truecolor")
    with console.status(f"[bold green]Fetching data for {args.username}...[/]"):
        weeks_data = fetch_contributions(args.username)
        stats = calculate_stats(weeks_data)
    
    display_heatmap(args.username, weeks_data, stats)

if __name__ == "__main__":
    main()