lint:
	flake8 .
	isort --recursive --check-only
	yapf --diff --parallel --recursive . | python -c 'import sys; result = sys.stdin.read(); assert not result, result;'
	mypy src/ tests/
	pydocstyle

clean:
	docker stop $(docker ps -a -q --filter="name=dcos-") | :
	docker rm --volumes $(docker ps -a -q --filter="name=dcos-") | :
	docker volume prune --force
	rm -rf /tmp/dcos-docker-*
