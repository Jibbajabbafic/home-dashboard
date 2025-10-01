import os
import re
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
BIN_PROPERTY_ID = os.getenv("BIN_PROPERTY_ID")
if not BIN_PROPERTY_ID:
    raise RuntimeError(
        "Environment variable BIN_PROPERTY_ID is required. Set it to the property ID from wasteservices.sheffield.gov.uk"
    )


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


# Bin collections are relatively static; cache for 12 hours
@cache_with_timeout(60 * 60 * 12)
def get_bin_collections() -> list[dict[str, str]]:
    """Scrape the Sheffield waste services property page for upcoming bin collections.

    Returns a list of dicts with keys: date (YYYY-MM-DD) and type (one of 'general', 'paper', 'glass').
    """
    url = f"https://wasteservices.sheffield.gov.uk/property/{BIN_PROPERTY_ID}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            html_content = response.read().decode("utf-8")
    except Exception as e:
        # In case of network or site error, return empty list
        print(f"Error fetching bin collections: {e}")
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    collections: list[dict[str, str]] = []

    # Targeted parsing for the Sheffield page table structure
    # Rows for services have classes like 'service-id-1' and contain a h4 with the bin name
    # and a td with class 'next-service' listing upcoming dates (comma separated)
    seen = set()
    table = soup.find("table", class_=lambda x: True if x else False)
    if table:
        # find rows with service-id-* in class
        for row in table.find_all("tr"):
            cls = row.get("class") or []
            cls_text = " ".join(cls)
            if "service-id-" in cls_text:
                # Find the bin name
                name_elem = row.find("h4")
                bin_name = name_elem.text.strip() if name_elem else ""
                # Map name to type
                low = bin_name.lower()
                if "black" in low or "residual" in low:
                    bin_type = "general"
                elif "blue" in low or "paper" in low or "card" in low:
                    bin_type = "paper"
                elif "brown" in low or "glass" in low or "cans" in low:
                    bin_type = "glass"
                else:
                    # unknown service, skip
                    bin_type = None

                # Find next-service td
                next_td = row.find("td", class_="next-service")
                if next_td and bin_type:
                    # normalize whitespace and remove header labels like 'Next Collections'
                    text = next_td.get_text(separator=" ").strip()
                    # Find all date-like substrings such as '2 Oct 2025' or '02 October 2025'
                    date_matches = re.findall(r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}", text)
                    for dm in date_matches:
                        parsed_dt = None
                        for fmt in ("%d %b %Y", "%d %B %Y"):
                            try:
                                parsed_dt = datetime.strptime(dm, fmt)
                                break
                            except Exception:
                                continue
                        if not parsed_dt:
                            continue
                        date_iso = parsed_dt.strftime("%Y-%m-%d")
                        key = f"{date_iso}:{bin_type}"
                        if key in seen:
                            continue
                        seen.add(key)
                        collections.append({"date": date_iso, "type": bin_type})

    # Only use the targeted parsing above which extracts rows with 'service-id-*'.

    # Sort collections by date
    try:
        collections.sort(key=lambda x: x["date"])
    except Exception:
        pass

    return collections


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
    bin_collections = get_bin_collections()
    return render_template(
        "index.html",
        times=times,
        fixtures=fixtures,
        bin_collections=bin_collections,
        stop_name=TRAM_STOP_NAME,
        football_team_name=FOOTBALL_TEAM_NAME,
    )


if __name__ == "__main__":
    # This is only used for development
    app.run(host="0.0.0.0", port=3000)
