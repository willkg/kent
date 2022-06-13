DEFAULT_GOAL := help
PROJECT=kent

.PHONY: help
help:
	@echo "Available rules:"
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:  /'

.PHONY: test
test:  ## Run tests and static typechecking
	tox

.PHONY: lint
lint:  ## Lint and black reformat files
	black --target-version=py37 --line-length=88 bin src tests setup.py
	flake8 bin src tests setup.py

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist src/${PROJECT}.egg-info .tox .pytest_cache
	find src/ -name __pycache__ | xargs rm -rf
	find src/ -name '*.pyc' | xargs rm -rf

.PHONY: checkrot
checkrot:  ## Check package rot for dev dependencies
	python -m venv ./tmpvenv/
	./tmpvenv/bin/pip install -U pip
	./tmpvenv/bin/pip install '.[dev]'
	./tmpvenv/bin/pip list -o
	rm -rf ./tmpvenv/

.PHONY: testdocker
testdocker:  ## Build Docker image and run it
	docker build --no-cache -t fakesentry:latest .
	docker run --rm --publish 5000:5000 fakesentry:latest run --host 0.0.0.0 --port 5000
