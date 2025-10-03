# Sheffield Home Dashboard

A simple web app dashboard for Sheffield homes, to show upcoming bus/tram times, football fixtures, and bin collection dates. Designed for integration with Home Assistant.

The app scrapes data from public websites to avoid relying on third-party paid APIs.

## Prerequisites

- Python 3.13+ (if running locally)
- `uv` (for managing Python dependencies and running the app)
- Docker & Docker Compose (optional, for container runs)

## Usage

Pre-built Docker images are available on Docker Hub: https://hub.docker.com/r/jibby/home-dashboard
It is recommended to use these Docker images for ease of setup and to avoid dependency issues. Make sure to set the required environment variables below.

### Required environment variables

- `BIN_PROPERTY_ID` (required): property ID used to fetch bin collection dates from wasteservices.sheffield.gov.uk. The app will raise an error if this is not set.
- `TRANSIT_STOP_ID` (optional): stop ID to use for transit scraping (default is provided).
- `FOOTBALL_TEAM_ID` (optional): team identifier used by the fixtures scraper (default is provided).
- `SHOW_DEBUG` (optional): set to `1`, `true`, or `yes` to show the in-page debug panel without enabling Flask's interactive debugger.

### Alternative ways to run

Run locally with UV:

```bash
make run
```

Run with Docker Compose:

```bash
make docker-run
```

### Debug & Development

There are two complementary debug options:

- `make dev` — recommended for active development. This runs Flask with `FLASK_DEBUG=1` (auto-reload and the interactive debugger) and also enables the in-page debug panel.
- `SHOW_DEBUG=1 make run` — shows the in-page debug panel only, without enabling Flask's interactive debugger. This is safer if you only need to inspect parsing and UI behavior.

Examples (zsh):

```bash
# Dev with auto-reload + Flask debugger + in-page debug panel
make dev

# Only enable in-page debug panel (no Flask interactive debugger)
SHOW_DEBUG=1 make run
```

Security note: Never enable Flask's interactive debugger on a publicly accessible/production server. Use these options only on your local machine or in a secured development environment.

## Mobile / Responsive

This release includes small responsive CSS improvements so the dashboard displays better on narrow screens (phones/tablets):

- Containers stack vertically on small screens instead of shrinking horizontally.
- Badges and dates wrap to avoid overflow.
- Reduced large hover transforms for touch devices.

To test locally, build and run with the normal `make run` workflow and open the page on a phone or in your browser's responsive mode.

## Debug panel (what it shows)

When enabled, the in-page debug panel displays:

- Parsed tram times as the client sees them
- Fixture list items (raw text and the parsed Date object)
- Parsed bin collection dates and badges
- Which fixture the countdown logic has selected as "relevant"

Use the debug panel to verify parsing rules, date formats, and to troubleshoot why a fixture is or is not being considered "ongoing".

## Troubleshooting

- If the app fails to start with an error about `BIN_PROPERTY_ID`, set that environment variable as shown above.

## Developer notes

- The app inlines `static/js/app.js` and `static/css/style.css` into the rendered page to make a single-file embed convenient for Home Assistant.
- For local development with auto-reload use `make dev` or the Flask CLI with `FLASK_DEBUG=1`.

## Contributing

Pull requests are welcome. For small fixes, open a PR with a focused change and a short description of the problem and solution.

## TODO

Potential future work:
- Support stops with multiple routes
- Make arrival times dynamic (don't hardcode)

