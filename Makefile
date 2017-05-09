lint:
	flake8 .
	isort --recursive --check-only
	yapf --diff --parallel --recursive . | python -c 'import sys; result = sys.stdin.read(); assert not result, result;'
	mypy src/ tests/
