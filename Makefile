.PHONY: all
all: test

.install-deps: $(shell find requirements -type f)
	@pip install -r requirements/dev.txt
	@pre-commit install
	@touch .install-deps

.develop: .install-deps $(shell find aiojobs -type f)
	@pip install -e .
	@touch .develop

.PHONY: setup
setup: .develop

.PHONY: lint
lint:
	pre-commit run --all-files
	mypy


.PHONY: test
test: .develop
	@pytest tests


.PHONY: cov
cov: .develop
	@PYTHONASYNCIODEBUG=1 pytest --cov=aiojobs tests
	@pytest --cov=aiojobs --cov-append --cov-report=html --cov-report=term tests
	@echo "open file://`pwd`/htmlcov/index.html"

.PHONY: doc
doc: .develop
	@make -C docs html SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"
