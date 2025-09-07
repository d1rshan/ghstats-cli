#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console

API_URL = "https://api.github.com/graphql"
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_contributions(username: str):
    if not TOKEN:
        print("❌ GITHUB_TOKEN not found. Put it in a .env or export it as env var.")
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
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = requests.post(API_URL, json={"query": query, "variables": {"login": username}}, headers=headers)
    if resp.status_code != 200:
        print("❌ HTTP error:", resp.status_code, resp.text)
        sys.exit(1)
    data = resp.json()
    if data.get("errors"):
        print("❌ GitHub API error:", data["errors"])
        sys.exit(1)

    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid = [[] for _ in range(7)]
    for week in weeks:
        for i, day in enumerate(week["contributionDays"]):
            grid[i].append(day["contributionCount"])
    return grid, weeks

def print_heatmap(grid, weeks):
    console = Console()
    colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

    month_labels = []
    last_month = None
    for week in weeks:
        first_day = week["contributionDays"][0]["date"]
        month = datetime.fromisoformat(first_day).strftime("%b")
        if month != last_month:
            month_labels.append(month)
            last_month = month
        else:
            month_labels.append("")

    month_row = "   " + " ".join([m.center(2) if m else "  " for m in month_labels])
    console.print(month_row)

    first_week_days = weeks[0]["contributionDays"]
    weekday_labels = [datetime.fromisoformat(d["date"]).strftime("%a") for d in first_week_days]

    for label, row in zip(weekday_labels, grid):
        cells = []
        for count in row:
            if count == 0:
                idx = 0
            elif count < 5:
                idx = 1
            elif count < 10:
                idx = 2
            elif count < 20:
                idx = 3
            else:
                idx = 4
            color = colors[idx]
            cells.append(f"[{color}]■[/]")
        console.print(f"{label} " + " ".join(cells))

def main():
    parser = argparse.ArgumentParser(description="GitHub contributions heatmap (terminal)")
    parser.add_argument("--user", "-u", required=True, help="GitHub username")
    args = parser.parse_args()

    grid, weeks = fetch_contributions(args.user)
    print_heatmap(grid, weeks)

if __name__ == "__main__":
    main()
