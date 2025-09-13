import requests
from datetime import datetime, timedelta, timezone
from rich.console import Console, Group
from rich.panel import Panel
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from rich.align import Align

API_URL = "https://api.github.com/graphql"


def fetch_contributions(username: str, token: str):
    """Fetch contribution data from GitHub GraphQL API."""
    if not token:
        raise RuntimeError("GitHub token not provided.")
    
    if not username:
        raise RuntimeError("Username not provided.")

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

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(
            API_URL, 
            json={"query": query, "variables": {"login": username}}, 
            headers=headers,
            timeout=30  
        )
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Please check your internet connection.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Connection error. Please check your internet connection.")
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            raise RuntimeError("Invalid GitHub token. Please check your token and try again.")
        elif resp.status_code == 403:
            raise RuntimeError("GitHub API rate limit exceeded or insufficient permissions.")
        else:
            raise RuntimeError(f"HTTP Error {resp.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}")

    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError("Invalid response from GitHub API.")

    if "errors" in data:
        error_msg = data['errors'][0].get('message', 'Unknown API error')
        if 'Could not resolve to a User' in error_msg:
            raise RuntimeError(f"User '{username}' not found on GitHub.")
        else:
            raise RuntimeError(f"GitHub API Error: {error_msg}")

    user_data = data.get("data", {}).get("user")
    if not user_data:
        raise RuntimeError(f"User '{username}' not found or no permission to view contributions.")

    try:
        weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
        return weeks
    except KeyError:
        raise RuntimeError("Unexpected API response format.")


def get_color_for_count(count: int, colors: list[str]) -> str:
    """Map contribution count to appropriate color."""
    if count == 0:
        return colors[0]  
    elif count < 5:
        return colors[1]
    elif count < 10:
        return colors[2]  
    elif count < 20:
        return colors[3]  
    else:
        return colors[4] 


def calculate_stats(weeks: list) -> dict:
    """Calculate contribution statistics from weekly data."""
    all_days = [day for week in weeks for day in week.get("contributionDays", [])]
    if not all_days:
        return {"total": 0, "longest_streak": 0, "current_streak": 0, "avg_daily": 0.0}

    all_days = sorted(all_days, key=lambda d: d["date"])
    total_contributions = sum(day["contributionCount"] for day in all_days)

    longest_streak = 0
    current_streak = 0
    temp_streak = 0

    for day in all_days:
        if day["contributionCount"] > 0:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

    today = datetime.now(timezone.utc).date()
    
    if all_days:
        last_day_date = datetime.fromisoformat(all_days[-1]["date"]).date()
        
        if last_day_date >= today - timedelta(days=2):
            for day in reversed(all_days):
                day_date = datetime.fromisoformat(day["date"]).date()
                if day["contributionCount"] > 0:
                    current_streak += 1
                else:
                    break
        else:
            current_streak = 0

    return {
        "total": total_contributions,
        "longest_streak": longest_streak,
        "current_streak": current_streak,
    }


def display_heatmap(username: str, weeks: list, stats: dict, colors: list[str], symbol: str):
    """Display the contribution heatmap with statistics."""
    console = Console(force_terminal=True, color_system="truecolor")
    
    title = f"GitHub Contributions for [bold cyan]{username}[/bold cyan]"
    
    stats_text = (
        f"[bold]{stats['total']:,}[/bold] contributions in the last year\n"
        f"Longest Streak: [bold green]{stats['longest_streak']} days[/bold green] 🗿\n"
        f"Current Streak: [bold green]{stats['current_streak']} days[/bold green] 🔥"
    )

    cell_width = len(symbol) + 1
    total_heatmap_width = len(weeks) * cell_width

    label_canvas = [' '] * total_heatmap_width
    last_month = None

    for i, week in enumerate(weeks):
        if not week.get("contributionDays"):
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
        days_in_week = {day['weekday']: day['contributionCount'] for day in week.get('contributionDays', [])}
        for day_idx in range(7):
            grid_data[day_idx].append(days_in_week.get(day_idx, 0))

    for day_idx in range(7):
        row_cells = []
        for count in grid_data[day_idx]:
            color = get_color_for_count(count, colors)
            row_cells.append(Text(symbol, style=color))
        heatmap_table.add_row(*row_cells)

    heatmap_with_bg = Padding(heatmap_table, (0, 1), style="on #000000")

    layout_table = Table.grid(expand=False, padding=0)
    layout_table.add_column(style="bold", justify="right")
    layout_table.add_column()
    layout_table.add_row(labels_table, Align.center(heatmap_with_bg))

    legend = Text("Less ", style="white")
    for color in colors:
        legend.append(symbol + " ", style=color)
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