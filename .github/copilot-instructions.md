# Copilot Instructions for AI Coding Agents

## Project Overview

This is a simple web app designed to display upcoming tram times and football fixtures, intended for integration with Home Assistant. The project is containerized and uses Docker for builds and execution.

## Architecture & Key Files

- `main.py`: Entry point for the application logic.
- `Dockerfile`, `compose.yaml`: Define the containerization and service orchestration.
- `run.sh`: Main script to build and run the app using Docker. This is the preferred workflow for local development and testing.
- `build_and_push.sh`: Used for building and pushing images, likely for deployment.
- `pyproject.toml`, `uv.lock`: Python dependencies and environment management.

## Developer Workflows

- **Build & Run:**
 - Use `make run` to build and start the app in Docker. This target handles all necessary setup.
- **Deployment:**
  - Use `build_and_push.sh` to build and push Docker images for deployment.
- **Configuration:**
  - Service configuration is managed via `compose.yaml` and environment variables (if any).

## Patterns & Conventions

- All application logic is centralized in `main.py`.
- Containerization is mandatory for local development and deployment; do not run Python scripts directly.
- Dependency management is handled via `pyproject.toml` and locked with `uv.lock`.
- Scripts (`run.sh`, `build_and_push.sh`) encapsulate all build and run logic—prefer using these over manual Docker commands.

## Integration Points

- The app is designed to work with Home Assistant, likely via API calls or data feeds (details may be in `main.py`).
- External dependencies are managed through Docker and Python package definitions.

## Examples

- To start development: `make run`
- To deploy: `./build_and_push.sh`

## Guidance for AI Agents

- Always use the provided scripts for builds and execution.
-
- When adding new dependencies, use the `uv` command and run the appropriate script to rebuild the environment.
- Keep all application logic in `main.py` unless refactoring for modularity.
- Reference `README.md` for the most up-to-date workflow instructions.

---

If any section is unclear or missing, please provide feedback for further refinement.
