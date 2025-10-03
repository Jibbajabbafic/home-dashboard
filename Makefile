.PHONY: run dev clean help docker-run docker-build

# Run using UV
run:
	uv run main.py

# Run in development mode with auto-reload
dev:
	FLASK_DEBUG=1 FLASK_APP=main.py uv run flask run --host=0.0.0.0 --port=3000

# Clean up any temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Run the app with Docker compose
docker-run:
	docker compose up --build

# Build and push Docker images (delegates to ./build_and_push.sh)
docker-build:
	./build_and_push.sh

# Full release process: bump version, build and push images
release:
	@echo "Starting release process..."
	./bump_tag.sh
	@echo "Building docker images..."
	./build_and_push.sh
	@echo "Release process complete."

# Show available targets
help:
	@echo "Available targets:"
	@echo "  run          - Run the application directly using uv"
	@echo "  clean        - Clean up temporary Python files"
	@echo "  docker-run   - Run the app using docker compose"
	@echo "  docker-build - Build and push images (calls './build_and_push.sh')"
	@echo "  release      - Full release process: bump version, build and push images"
	@echo "  help         - Show this help message"

# Set docker-run as the default target
.DEFAULT_GOAL := docker-run