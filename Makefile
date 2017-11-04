all: test

isort:
	isort -rc

flake8:
	@flake8 .
	isort -rc -c

test: flake8
	@pytest tests


cov: flake8
	@PYTHONASYNCIODEBUG=1 pytest --cov=aiojobs tests
	@pytest --cov=aiojobs --cov-append --cov-report=html --cov-report=term tests
	@echo "open file://`pwd`/htmlcov/index.html"

doc:
	@make -C docs html SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"
