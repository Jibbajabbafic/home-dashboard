import urllib.request
from html.parser import HTMLParser


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


def main():
    url = "https://connect.wyca.vix-its.com/Text/WebDisplay.aspx?stopRef=9400ZZSYMID1&stopName=Middlewood+To+City"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode("utf-8")

    parser = TramTimeParser()
    parser.feed(html_content)

    print("Next tram times:")
    for time in parser.tram_times:
        print(time)


if __name__ == "__main__":
    main()
