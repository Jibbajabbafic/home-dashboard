# Home Dashboard
A simple web app to show upcoming tram times and football fixtures in Home Assistant.

## Development
Run `make run` to build and run the app using docker.

## Mobile / Responsive

This release includes small responsive CSS improvements so the dashboard displays better on narrow screens (phones/tablets):

- Containers stack vertically on small screens instead of shrinking horizontally.
- Badges and dates wrap to avoid overflow.
- Reduced large hover transforms for touch devices.

To test locally, build and run with the normal `make run` workflow and open the page on a phone or in your browser's responsive mode.

# TODO
Potential future work
- Auto detect bus or tram and change naming/emoji
- Support stops with multiple routes
- Make arrival times dynamic (don't hardcode)

