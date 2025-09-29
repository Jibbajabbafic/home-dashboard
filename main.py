import urllib.request
from flask import Flask, render_template_string
from bs4 import BeautifulSoup
from datetime import datetime


def get_tram_times():
    url = "https://connect.wyca.vix-its.com/Text/WebDisplay.aspx?stopRef=9400ZZSYMID1&stopName=Middlewood+To+City"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode("utf-8")

    soup = BeautifulSoup(html_content, "html.parser")
    tram_times = []

    # Find the timetable with class webDisplayTable
    table = soup.find("table", class_="webDisplayTable")
    if table:
        # Skip the header row and get all data rows
        rows = table.find_all("tr")[1:]  # Skip header row
        for row in rows:
            # The time is in the third cell
            cells = row.find_all("td")
            if len(cells) >= 3:
                time = cells[2].text.strip()
                if time:
                    tram_times.append(time)

    return tram_times


def get_football_fixtures():
    fixture_limit = 5
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
            # Limit the number of fixtures
            if len(fixtures) >= fixture_limit:
                break
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
    <meta http-equiv="refresh" content="300">
    <style>
        :root {
            --primary: #2c3e50;
            --secondary: #34495e;
            --accent: #3498db;
            --text: #2c3e50;
            --light: #ecf0f1;
            --shadow: rgba(0, 0, 0, 0.1);
        }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            display: flex;
            flex-direction: column;
            margin: 0;
            background: var(--light);
            color: var(--text);
            min-height: 100vh;
        }
        .clock {
            text-align: center;
            font-size: 2.5em;
            padding: 20px;
            background: var(--primary);
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px var(--shadow);
        }
        .container-row {
            display: flex;
            gap: 20px;
            padding: 0 20px;
        }
        .container {
            flex: 1;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px var(--shadow);
        }
        .countdown {
            font-size: 1.2em;
            color: var(--accent);
            margin-bottom: 20px;
            text-align: center;
            padding: 10px;
            background: var(--light);
            border-radius: 5px;
            font-weight: 500;
        }
        h1, h2 {
            color: var(--primary);
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        ul {
            list-style-type: none;
            padding: 0;
            margin: 0;
        }
        li {
            background: var(--light);
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            transition: all 0.2s ease-in-out;
            border-left: 4px solid transparent;
        }
        li:hover {
            transform: translateX(5px);
        }
        li.imminent {
            background: #fff3cd;
            border-left-color: #ffc107;
            animation: pulse 2s ease-in-out infinite;
            position: relative;
            overflow: hidden;
        }
        li.imminent::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 193, 7, 0.2);
            animation: shine 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.01); }
            100% { transform: scale(1); }
        }
        @keyframes shine {
            0% { opacity: 0; }
            50% { opacity: 1; }
            100% { opacity: 0; }
        }
        small {
            color: var(--secondary);
            display: block;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="clock" id="clock">00:00:00</div>
    <div class="container-row">
        <div class="container">
            <div class="countdown" id="nextTramCountdown">Next tram in: calculating...</div>
            <h1>🚊 Tram Times</h1>
            <h3>Departures from: Middlewood To City</h3>
            <ul>
                {% for time in times %}
                    <li>{{ time }}</li>
                {% endfor %}
            </ul>
        </div>
        <div class="container">
            <div class="countdown" id="nextFixtureCountdown">Next match in: calculating...</div>
            <h1>⚽ Upcoming Fixtures</h1>
            <h3>Sheffield Wednesday Home Matches</h3>
            <ul>
                {% for fixture in fixtures %}
                    <li>
                        {% if fixture.competition %}{{ fixture.competition }} - {% endif %}
                        {% set date = fixture.date.split('-') %}
                        {% set time = fixture.time.split(':') %}
                        {{ date[2] }}/{{ date[1] }}/{{ date[0] }} at {{ time[0] }}:{{ time[1] }} - vs {{ fixture.away_team }}<br>
                    </li>
                {% endfor %}
            </ul>
        </div>
    </div>
    <script>
        // Update clock
        function updateClock() {
            const now = new Date();
            document.getElementById('clock').textContent = now.toTimeString().split(' ')[0];
        }
        setInterval(updateClock, 1000);
        updateClock();

        // Parse times and update countdowns
        function parseTime(timeStr) {
            const [hours, minutes] = timeStr.split(':');
            const now = new Date();
            const target = new Date(now.getFullYear(), now.getMonth(), now.getDate(), parseInt(hours), parseInt(minutes));
            if (target < now) {
                target.setDate(target.getDate() + 1);
            }
            return target;
        }

        function getNextTramTime() {
            const times = [{% for time in times %}'{{ time }}',{% endfor %}];
            const now = new Date();
            let nextTime = null;

            for (const time of times) {
                const tramTime = parseTime(time);
                if (tramTime > now) {
                    if (!nextTime || tramTime < nextTime) {
                        nextTime = tramTime;
                    }
                }
            }
            return nextTime;
        }

        function getNextFixtureTime() {
            const fixtures = [
                {% for fixture in fixtures %}
                {
                    date: '{{ fixture.date }}',
                    time: '{{ fixture.time }}'
                },
                {% endfor %}
            ];
            const now = new Date();
            let nextTime = null;

            for (const fixture of fixtures) {
                const [year, month, day] = fixture.date.split('-');
                const [hours, minutes] = fixture.time.split(':');
                const fixtureTime = new Date(year, parseInt(month) - 1, day, hours, minutes);

                if (fixtureTime > now) {
                    if (!nextTime || fixtureTime < nextTime) {
                        nextTime = fixtureTime;
                    }
                }
            }
            return nextTime;
        }

        function updateCountdowns() {
            const now = new Date();

            // Update tram countdown and remove passed times
            const times = [...document.querySelectorAll('.container:first-of-type ul li')]
                .map(li => li.textContent.trim());

            // Remove passed tram times and highlight imminent ones
            times.forEach(time => {
                if (!time) return; // Skip if time is invalid
                const tramTime = parseTime(time);
                if (!tramTime) return; // Skip if parsing failed

                const listItems = document.querySelectorAll('.container:first-of-type ul li');
                if (!listItems.length) return; // Skip if no items found

                listItems.forEach(item => {
                    if (item && item.textContent && item.textContent.trim() === time) {
                        if (tramTime < now) {
                            item.remove();
                        } else {
                            // Check if tram is within 10 minutes
                            const timeDiff = tramTime - now;
                            const minutesUntil = Math.floor(timeDiff / 60000);
                            if (minutesUntil <= 10) {
                                item.classList.add('imminent');
                            } else {
                                item.classList.remove('imminent');
                            }
                        }
                    }
                });
            });

            // Highlight today's fixtures
            const fixtureItems = document.querySelectorAll('.container:nth-of-type(2) ul li');
            if (fixtureItems.length) { // Only process if we found fixture items
                fixtureItems.forEach(item => {
                    const smallElement = item.querySelector('small');
                    if (!smallElement || !smallElement.textContent) return; // Skip if no small element or no text

                    const dateText = smallElement.textContent;
                    const datePart = dateText.split(' at ')[0];
                    if (!datePart) return; // Skip if no date part

                    const dateParts = datePart.split('/');
                    if (dateParts.length !== 3) return; // Skip if date format is invalid

                    const [day, month, year] = dateParts;
                    const fixtureDate = new Date(year, month - 1, day);

                    if (fixtureDate.toDateString() === now.toDateString()) {
                        item.classList.add('imminent');
                    } else {
                        item.classList.remove('imminent');
                    }
                });
            }            // Update countdown for next tram
            const nextTram = getNextTramTime();
            if (nextTram) {
                const diffTram = Math.max(0, nextTram - now);
                const minutesTram = Math.floor(diffTram / 60000);
                const secondsTram = Math.floor((diffTram % 60000) / 1000);
                document.getElementById('nextTramCountdown').textContent =
                    `Next tram in: ${minutesTram}m ${secondsTram}s`;
            } else {
                document.getElementById('nextTramCountdown').textContent = 'No upcoming trams';
            }

            // Update fixture countdown
            const nextFixture = getNextFixtureTime();
            if (nextFixture) {
                const diffFixture = Math.max(0, nextFixture - now);
                const daysFix = Math.floor(diffFixture / (1000 * 60 * 60 * 24));
                const hoursFix = Math.floor((diffFixture % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutesFix = Math.floor((diffFixture % (1000 * 60 * 60)) / (1000 * 60));
                document.getElementById('nextFixtureCountdown').textContent =
                    `Next match in: ${daysFix}d ${hoursFix}h ${minutesFix}m`;
            }
        }
        // Initial update to prevent "calculating..." message
        updateCountdowns();
        // Then set up the interval for continuous updates
        setInterval(updateCountdowns, 1000);
    </script>
</body>
</html>"""


@app.route("/")
def index():
    times = get_tram_times()
    fixtures = get_football_fixtures()
    return render_template_string(HTML_TEMPLATE, times=times, fixtures=fixtures)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
