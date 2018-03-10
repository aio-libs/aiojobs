all: test

isort:
	isort -rc


.install-deps: $(shell find requirements -type f)
	@pip install -r requirements/dev.txt
	@touch .install-deps

.develop: .install-deps $(shell find aiojobs -type f)
	@flit install --symlink
	@touch .develop

.flake: .install-deps .develop $(shell find aiojobs -type f) \
                      $(shell find tests -type f)
	@flake8 .
	@isort -rc -c
	@touch .flake

flake: .flake

test: flake
	@pytest tests


cov: flake
	@PYTHONASYNCIODEBUG=1 pytest --cov=aiojobs tests
	@pytest --cov=aiojobs --cov-append --cov-report=html --cov-report=term tests
	@echo "open file://`pwd`/htmlcov/index.html"

doc:
	@make -C docs html SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"
