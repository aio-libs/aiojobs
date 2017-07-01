flake8:
	@flake8 .

test:
	@pytest tests


cov:
	@pytest --cov=aiojobs --cov-report=term tests
	@echo "open file://`pwd`/htmlcov/index.html"
