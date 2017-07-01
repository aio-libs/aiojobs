flake8:
	@flake8 .

test:
	@pytest tests


cov:
	@pytest --cov=aiojobs --cov-report=html tests
	@echo "open file://`pwd`/htmlcov/index.html"
