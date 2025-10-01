import os
import time
import urllib.request
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Tuple

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, Response, render_template

# Load environment variables
load_dotenv()

# Get configuration with defaults
TRAM_STOP_REF = os.getenv("TRAM_STOP_REF", "9400ZZSYMID1")
TRAM_STOP_NAME = os.getenv("TRAM_STOP_NAME", "Middlewood To City")
FOOTBALL_TEAM_ID = os.getenv("FOOTBALL_TEAM_ID", "sheffield-wednesday")
FOOTBALL_TEAM_NAME = os.getenv("FOOTBALL_TEAM_NAME", "Sheffield Wednesday")


# Cache decorator with timeout
def cache_with_timeout(
    timeout_seconds: int,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """A simple caching decorator with a timeout in seconds.

    Args:
        timeout_seconds: Number of seconds to keep a cached value.

    Returns:
        A decorator that caches function results.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache: Dict[str, Tuple[Any, float]] = {}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()

            # Check if we have a cached value and it's still valid
            if func.__name__ in cache:
                result, timestamp = cache[func.__name__]
                if now - timestamp < timeout_seconds:
                    return result

            # If no cache or expired, call the function and cache the result
            result = func(*args, **kwargs)
            cache[func.__name__] = (result, now)
            return result

        return wrapper

    return decorator


@cache_with_timeout(30)  # Cache tram times for 30 seconds
def get_tram_times() -> list[tuple[str, str, str, str]]:
    # Construct URL with environment variables
    url = f"https://bustimes.org/stops/{TRAM_STOP_REF}"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode("utf-8")

    soup = BeautifulSoup(html_content, "html.parser")
    tram_times: list[tuple[str, str, str, str]] = []

    # Find all tables - multiple if spread across days
    tables = soup.find_all("table")
    for table in tables:
        # Skip the header row and get all data rows
        rows = table.find_all("tr")[1:]  # Skip header row
        for row in rows:
            # The time is in the third cell
            cells = row.find_all("td")
            if len(cells) >= 3:
                time_str = cells[2].text.strip()
                if time_str:
                    parsed_time = datetime.strptime(time_str, "%H:%M")
                    kelham_time = parsed_time + timedelta(minutes=12)
                    university_time = parsed_time + timedelta(minutes=16)
                    cathedral_time = parsed_time + timedelta(minutes=20)
                    tram_times.append(
                        (
                            time_str,
                            kelham_time.strftime("%H:%M"),
                            university_time.strftime("%H:%M"),
                            cathedral_time.strftime("%H:%M"),
                        )
                    )

    return tram_times


@cache_with_timeout(3600)  # Cache fixtures for 1 hour
def get_football_fixtures() -> list[dict[str, str]]:
    fixture_limit = 5
    url = f"https://fixtur.es/en/team/{FOOTBALL_TEAM_ID}/home"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode("utf-8")

    soup = BeautifulSoup(html_content, "html.parser")
    fixtures: list[dict[str, str]] = []
    today = datetime.now().date()

    # Find the fixtures container
    fixtures_div = soup.find("div", class_="wedstrijden")
    if fixtures_div:
        # Find all fixture divs (they start with fi_event_)
        for item in fixtures_div.find_all(
            "div", id=lambda x: bool(x and x.startswith("fi_event_"))
        ):
            # Limit the number of fixtures
            if len(fixtures) >= fixture_limit:
                break
            # Get the competition from img title if it exists
            competition = ""
            img = item.find("img")
            if img and img.get("title"):
                competition = str(img.get("title"))

            # Find the date and time
            time_elem = item.find("time")
            date = ""
            time_str = ""
            if time_elem:
                dt_attr = time_elem.get("datetime", "")
                date_time = str(dt_attr).split("T")
                if date_time:
                    date = date_time[0]
                    if len(date_time) > 1:
                        time_str = date_time[1].split("+")[0]

            # Skip this fixture if it's in the past
            if date:
                fixture_date = datetime.strptime(str(date), "%Y-%m-%d").date()
                if fixture_date < today:
                    continue

            # Find the teams div - it's the one that contains a dash
            game_divs = item.find_all("div")
            for div in game_divs:
                text = div.text.strip()
                if "-" in text:
                    teams = text.split("-")
                    home_team = teams[0].strip()
                    away_team = teams[1].strip()

                    fixtures.append(
                        {
                            "competition": str(competition),
                            "date": str(date),
                            "time": str(time_str),
                            "home_team": str(home_team),
                            "away_team": str(away_team),
                        }
                    )
                    break

    return fixtures


app = Flask(__name__)

# The HTML, CSS and JS are moved to `templates/index.html` and `static/`.


# Configure Flask app for production
app.config["SECRET_KEY"] = "dev"
app.config["PREFERRED_URL_SCHEME"] = "http"


# Allow iframe embedding for Home Assistant
@app.after_request
def after_request(response: Response) -> Response:
    response.headers["X-Frame-Options"] = "ALLOWALL"
    return response


@app.route("/")
def index():
    times = get_tram_times()
    fixtures = get_football_fixtures()
    return render_template(
        "index.html",
        times=times,
        fixtures=fixtures,
        stop_name=TRAM_STOP_NAME,
        football_team_name=FOOTBALL_TEAM_NAME,
    )


if __name__ == "__main__":
    # This is only used for development
    app.run(host="0.0.0.0", port=3000)
