.PHONY: run clean help docker-run docker-build

# Default target
run:
	uv run main.py

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

# Show available targets
help:
	@echo "Available targets:"
	@echo "  run          - Run the application directly using uv"
	@echo "  clean        - Clean up temporary Python files"
	@echo "  docker-run   - Run the app using docker compose"
	@echo "  docker-build - Build and push images (calls './build_and_push.sh')"
	@echo "  help         - Show this help message"

# Set run as the default target
.DEFAULT_GOAL := docker-run