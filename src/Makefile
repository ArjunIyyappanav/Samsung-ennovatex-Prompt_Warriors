# Makefile for On-Device Agentic Battery Optimization System

.PHONY: help setup install demo dashboard clean test lint format docs

# Default target
help:
	@echo "🔋 On-Device Agentic Battery Optimization System"
	@echo "Available commands:"
	@echo "  setup      - Set up the project (install dependencies, create directories)"
	@echo "  install    - Install Python dependencies only"
	@echo "  demo       - Run the full system demonstration"
	@echo "  dashboard  - Start the web dashboard"
	@echo "  agent      - Start the agent system"
	@echo "  video      - Start the demo video player"
	@echo "  test       - Run basic functionality tests"
	@echo "  clean      - Clean up generated files and logs"
	@echo "  lint       - Run code linting"
	@echo "  format     - Format code with black"
	@echo "  docs       - Generate documentation"

# Setup the project
setup:
	@echo "🔧 Setting up battery optimization system..."
	python setup.py

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

# Run full demonstration
demo:
	@echo "🎬 Starting full system demonstration..."
	python test_system.py

# Start web dashboard
dashboard:
	@echo "📊 Starting web dashboard..."
	python -c "from dashboard.web_dashboard import WebDashboard; from core.agent_controller import AgentController; d = WebDashboard(AgentController()); d.start(threaded=False)"

# Start agent system
agent:
	@echo "🤖 Starting agent system..."
	python main.py --dashboard

# Start demo video player
video:
	@echo "🎥 Starting demo video player..."
	python demo_app/video_player.py

# Run basic tests
test:
	@echo "🧪 Running basic functionality tests..."
	python -c "from setup import run_basic_test; run_basic_test()"

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	rm -rf models/*.pkl
	rm -rf logs/*.log
	rm -rf __pycache__
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Run linting (if flake8 is available)
lint:
	@echo "🔍 Running code linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 core/ demo_app/ dashboard/ utils/ --max-line-length=100 --ignore=E203,W503; \
	else \
		echo "⚠️  flake8 not installed. Install with: pip install flake8"; \
	fi

# Format code (if black is available)
format:
	@echo "✨ Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black core/ demo_app/ dashboard/ utils/ --line-length=100; \
	else \
		echo "⚠️  black not installed. Install with: pip install black"; \
	fi

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "Documentation is available in README.md"
	@echo "API documentation can be found in the source code docstrings"

# Development targets
dev-install:
	@echo "🛠️  Installing development dependencies..."
	pip install flake8 black pytest

# Quick start target
quick-start: setup demo

# Create release package
package:
	@echo "📦 Creating release package..."
	tar -czf battery-optimization-system.tar.gz \
		--exclude=__pycache__ \
		--exclude=*.pyc \
		--exclude=logs \
		--exclude=models \
		core/ demo_app/ dashboard/ utils/ config/ \
		*.py *.txt *.md Makefile
	@echo "✅ Package created: battery-optimization-system.tar.gz"

# Install system dependencies (Linux)
install-system-deps:
	@echo "📦 Installing system dependencies (Linux)..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y python3-dev python3-pip; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum install -y python3-devel python3-pip; \
	else \
		echo "⚠️  Please install Python 3.8+ and pip manually"; \
	fi

# Show system status
status:
	@echo "📊 System Status:"
	@echo "Python version: $$(python --version)"
	@echo "Platform: $$(python -c 'import platform; print(platform.system())')"
	@echo "Available memory: $$(python -c 'import psutil; print(f\"{psutil.virtual_memory().available // 1024 // 1024} MB\")')" 2>/dev/null || echo "psutil not available"
	@echo "Battery status: $$(python -c 'import psutil; b=psutil.sensors_battery(); print(f\"{b.percent}% ({'charging' if b.power_plugged else 'discharging'})\" if b else \"No battery info\")')" 2>/dev/null || echo "Battery info not available"
