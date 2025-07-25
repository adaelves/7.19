# VideoDownloader Makefile
# Provides convenient commands for building and testing

.PHONY: help install test test-portable build-portable build-all clean lint format

# Default target
help:
	@echo "VideoDownloader Build System"
	@echo "============================"
	@echo ""
	@echo "Available commands:"
	@echo "  install        - Install dependencies"
	@echo "  test           - Run all tests"
	@echo "  test-portable  - Run portable-specific tests"
	@echo "  build-portable - Build portable version for current platform"
	@echo "  build-all      - Build portable versions for all platforms"
	@echo "  clean          - Clean build directories"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code"
	@echo "  demo-portable  - Run portable functionality demo"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install pyinstaller
	pip install PySide6 requests aiohttp yt-dlp
	pip install pytest pytest-qt pytest-asyncio pytest-cov
	pip install black flake8 isort
	@echo "Dependencies installed successfully!"

# Run all tests
test:
	@echo "Running all tests..."
	python -m pytest tests/ -v --tb=short

# Run portable-specific tests
test-portable:
	@echo "Running portable tests..."
	python -m pytest tests/test_portable_build.py -v

# Build portable version for current platform
build-portable:
	@echo "Building portable version..."
	python build_portable.py --verbose

# Build portable versions for all platforms
build-all:
	@echo "Building portable versions for all platforms..."
	python build_portable.py --platform all --verbose

# Clean build directories
clean:
	@echo "Cleaning build directories..."
	@if exist build rmdir /s /q build
	@if exist dist rmdir /s /q dist
	@if exist portable rmdir /s /q portable
	@if exist __pycache__ rmdir /s /q __pycache__
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
	@echo "Build directories cleaned!"

# Run code linting
lint:
	@echo "Running code linting..."
	python -m flake8 app/ build_scripts/ tests/ --max-line-length=100 --ignore=E203,W503
	@echo "Linting completed!"

# Format code
format:
	@echo "Formatting code..."
	python -m black app/ build_scripts/ tests/ --line-length=100
	python -m isort app/ build_scripts/ tests/ --profile=black
	@echo "Code formatting completed!"

# Run portable functionality demo
demo-portable:
	@echo "Running portable functionality demo..."
	python examples/portable_demo.py

# Run compatibility tests
test-compatibility:
	@echo "Running cross-platform compatibility tests..."
	python tests/run_compatibility_tests.py --verbose

# Quick development setup
dev-setup: install
	@echo "Setting up development environment..."
	@if not exist Data mkdir Data
	@if not exist Data\Config mkdir Data\Config
	@if not exist Data\Cache mkdir Data\Cache
	@if not exist Data\Logs mkdir Data\Logs
	@if not exist Data\Downloads mkdir Data\Downloads
	@echo "Development environment ready!"

# Package information
info:
	@echo "VideoDownloader Package Information"
	@echo "=================================="
	@echo "Version: 1.0.0"
	@echo "Platform: Windows/macOS/Linux"
	@echo "Python: 3.8+"
	@echo "License: Open Source"
	@echo ""
	@echo "Build Status:"
	@python -c "import sys; print(f'Python: {sys.version}')"
	@python -c "try: import PySide6; print('✓ PySide6 available'); except: print('✗ PySide6 missing')"
	@python -c "try: import PyInstaller; print('✓ PyInstaller available'); except: print('✗ PyInstaller missing')"
	@python -c "try: import requests; print('✓ requests available'); except: print('✗ requests missing')"

# Create release package
release: clean test build-all
	@echo "Creating release package..."
	@echo "All builds completed successfully!"
	@echo "Release packages available in portable/ directory"

# Development workflow
dev: dev-setup test-portable demo-portable
	@echo "Development workflow completed!"
	@echo "Ready for development!"