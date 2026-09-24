.PHONY: help install test lint format typecheck check clean

PYTHON ?= python

help:
	@echo "Hospital Readmission AI - Available Commands:"
	@echo "  make install    : Install production dependencies"
	@echo "  make install-dev: Install all dependencies (production + development)"
	@echo "  make test       : Run test suite with pytest"
	@echo "  make lint       : Run linter checks (Ruff)"
	@echo "  make format     : Run formatters (Black & Ruff fix)"
	@echo "  make typecheck  : Run static type checks (Mypy)"
	@echo "  make check      : Run all checks (lint, typecheck, test)"
	@echo "  make clean      : Remove cache and temporary build artifacts"

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m black .
	$(PYTHON) -m ruff check --fix .

typecheck:
	$(PYTHON) -m mypy src tests

check: lint typecheck test

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').glob('.pytest_cache')]"
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').glob('.mypy_cache')]"
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').glob('.ruff_cache')]"
