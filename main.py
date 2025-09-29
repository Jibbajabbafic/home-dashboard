import urllib.request
from html.parser import HTMLParser
from flask import Flask, render_template_string
from bs4 import BeautifulSoup
from datetime import datetime


class TramTimeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.tram_times = []
        self.cell_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            for attr, value in attrs:
                if attr == "class" and "webDisplayTable" in value:
                    self.in_table = True
        if self.in_table and tag == "tr":
            self.in_row = True
            self.cell_count = 0
        if self.in_row and tag == "td":
            self.in_cell = True

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        if tag == "tr":
            self.in_row = False
        if tag == "td":
            self.in_cell = False

    def handle_data(self, data):
        if self.in_cell:
            self.cell_count += 1
            if self.cell_count == 3:  # The time is in the third cell
                time = data.strip()
                if time:
                    self.tram_times.append(time)


def get_tram_times():
    url = "https://connect.wyca.vix-its.com/Text/WebDisplay.aspx?stopRef=9400ZZSYMID1&stopName=Middlewood+To+City"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode("utf-8")

    parser = TramTimeParser()
    parser.feed(html_content)
    return parser.tram_times


def get_football_fixtures():
    url = "https://fixtur.es/en/team/sheffield-wednesday/home"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode("utf-8")

    soup = BeautifulSoup(html_content, "html.parser")
    fixtures = []
    today = datetime.now().date()

    # Find the fixtures container
    fixtures_div = soup.find("div", class_="wedstrijden")
    if fixtures_div:
        # Find all fixture divs (they start with fi_event_)
        for item in fixtures_div.find_all(
            "div", id=lambda x: x and x.startswith("fi_event_")
        ):
            # Get the competition from img title if it exists
            competition = ""
            img = item.find("img")
            if img and img.get("title"):
                competition = img.get("title")

            # Find the date and time
            time_elem = item.find("time")
            date = ""
            time = ""
            if time_elem:
                date_time = time_elem.get("datetime", "").split("T")
                if date_time:
                    date = date_time[0]
                    if len(date_time) > 1:
                        time = date_time[1].split("+")[0]

            # Skip this fixture if it's in the past
            if date:
                fixture_date = datetime.strptime(date, "%Y-%m-%d").date()
                if fixture_date < today:
                    continue

            # Find the teams div - it's the one that contains a dash
            game_divs = item.find_all("div")
            for div in game_divs:
                text = div.text.strip()
                if "-" in text and "Sheffield Wednesday" in text:
                    teams = text.split("-")
                    home_team = "Sheffield Wednesday"
                    away_team = teams[1].strip()

                    fixtures.append(
                        {
                            "competition": competition,
                            "date": date,
                            "time": time,
                            "home_team": home_team,
                            "away_team": away_team,
                        }
                    )
                    break

    return fixtures


app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: sans-serif; display: flex; }
        .container { flex: 1; padding: 10px; }
        h1, h2 { color: #333; }
        ul { list-style-type: none; padding: 0; }
        li { background: #f4f4f4; margin: 5px 0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Next Tram Times</h1>
        <ul>
            {% for time in times %}
                <li>{{ time }}</li>
            {% endfor %}
        </ul>
    </div>
    <div class="container">
        <h2>Upcoming Fixtures</h2>
        <ul>
            {% for fixture in fixtures %}
                <li>
                    {{ fixture.home_team }} vs {{ fixture.away_team }}<br>
                    <small>
                        {% if fixture.competition %}{{ fixture.competition }} - {% endif %}
                        {% set date = fixture.date.split('-') %}
                        {{ date[2] }}/{{ date[1] }}/{{ date[0] }} at {{ fixture.time }}
                    </small>
                </li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    times = get_tram_times()
    fixtures = get_football_fixtures()
    return render_template_string(HTML_TEMPLATE, times=times, fixtures=fixtures)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
