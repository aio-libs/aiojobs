all: test

flake8:
	@flake8 .

test: flake8
	@pytest tests


cov: flake8
	@pytest --cov=aiojobs --cov-report=html tests
	@echo "open file://`pwd`/htmlcov/index.html"

doc:
	@make -C docs html SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"
