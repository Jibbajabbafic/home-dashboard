import urllib.request
from html.parser import HTMLParser
from flask import Flask, render_template_string


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


app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Tram Times</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: sans-serif; }
        h1 { color: #333; }
        ul { list-style-type: none; padding: 0; }
        li { background: #f4f4f4; margin: 5px 0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Next Tram Times</h1>
    <ul>
        {% for time in times %}
            <li>{{ time }}</li>
        {% endfor %}
    </ul>
</body>
</html>
"""


@app.route("/")
def index():
    times = get_tram_times()
    return render_template_string(HTML_TEMPLATE, times=times)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
