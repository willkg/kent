DEFAULT_GOAL := help
PROJECT=kent

.PHONY: help
help:
	@echo "Available rules:"
	@echo ""
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:  /'

.PHONY: build
build: clean lint test  ## Build sdist and wheel for distribution
	check-manifest
	python -m build
	echo ""
	echo "Run: git tag -s TAGNAME"
	echo ""
	echo "Run: twine upload -r kent dist/*"
	echo ""
	echo "Push tag to GitHub."

.PHONY: test
test:  ## Run tests and static typechecking
	tox

.PHONY: lint
lint:  ## Lint and black reformat files
	black bin src tests
	tox -e py38-lint

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist src/${PROJECT}.egg-info .tox .pytest_cache
	find src/ -name __pycache__ | xargs rm -rf
	find src/ -name '*.pyc' | xargs rm -rf

.PHONY: checkrot
checkrot:  ## Check package rot for dev dependencies
	python -m venv ./tmpvenv/
	./tmpvenv/bin/pip install -U pip
	./tmpvenv/bin/pip install -r requirements-dev.txt
	./tmpvenv/bin/pip list -o
	rm -rf ./tmpvenv/

.PHONY: testdocker
testdocker:  ## Build Docker image and run it
	docker build --no-cache -t kent:latest .
	docker run --init --rm --publish 5000:5000 kent:latest run --host 0.0.0.0 --port 5000
