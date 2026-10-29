# Local developer shortcuts. Run `make help` for the list of targets.
PY ?= python3
VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := $(shell command -v uv 2>/dev/null)

.PHONY: help setup test validate run clean

help:
	@echo "make setup     create $(VENV) and install dev dependencies (uv if available)"
	@echo "make test      run the offline test suite"
	@echo "make validate  validate Actor schemas with the Apify CLI"
	@echo "make run       live local run with the default input"
	@echo "make clean     remove the venv and local storage"

setup:
ifeq ($(UV),)
	$(PY) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
else
	uv venv $(VENV) --python 3.12
	uv pip install --python $(PYTHON) -r requirements-dev.txt
endif
	@echo "Environment ready. Activate it with: source $(VENV)/bin/activate"

test:
	$(PYTHON) -m pytest

validate:
	apify validate-schema

# Force the venv interpreter onto PATH so the CLI cannot fall back to a
# Homebrew or system python that lacks the dependencies.
run:
	PATH=$(CURDIR)/$(VENV)/bin:$$PATH apify run --purge

clean:
	rm -rf $(VENV) storage .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
