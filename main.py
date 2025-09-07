import os
import sys
import requests
from rich.console import Console
from rich.table import Table
from rich import box
from dotenv import load_dotenv
import argparse

API_URL = "https://api.github.com/graphql"

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_contributions(username: str):
    if not TOKEN:
        print("❌ Please set GITHUB_TOKEN env var with your GitHub personal access token")
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
    response = requests.post(API_URL, json={"query": query, "variables": {"login": username}}, headers=headers)

    if response.status_code != 200:
        print("❌ Error fetching data:", response.text)
        sys.exit(1)

    weeks = response.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

    grid = []
    for week in weeks:
        for i, day in enumerate(week["contributionDays"]):
            if len(grid) <= i:
                grid.append([])
            grid[i].append(day["contributionCount"])
    return grid  


from rich.console import Console
from rich.table import Table
from rich import box

def print_heatmap(grid):
    console = Console()
    table = Table(show_header=False, show_lines=False, box=box.MINIMAL, padding=(0, 0))

    colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

    for row in grid:
        table.add_row(*[
            f"[{colors[min(4, count // 5)]}]■[/]" if count > 0 else "[#ebedf0]■[/]"
            for count in row
        ])

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="GitHub Contributions Heatmap in Terminal")
    parser.add_argument("--user", required=True, help="GitHub username")
    args = parser.parse_args()

    grid = fetch_contributions(args.user)
    print_heatmap(grid)


if __name__ == "__main__":
    main()
