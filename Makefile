ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh
DCOS_DOCKER_REPOSITORY := https://github.com/adamtheturtle/dcos-docker.git
DCOS_DOCKER_BRANCH := macos-DCOS-15645

# Run various linting tools.
lint:
	flake8 .
	isort --recursive --check-only
	yapf --diff --parallel --recursive . | python -c 'import sys; result = sys.stdin.read(); assert not result, result;'
	mypy src/ tests/
	pydocstyle

# Attempt to clean leftovers by the test suite.
clean:
	docker stop $$(docker ps -a -q --filter="name=dcos-") | :
	docker rm --volumes $$(docker ps -a -q --filter="name=dcos-") | :
	docker volume prune --force
	rm -rf /tmp/dcos-docker-*

# Fix some linting errors.
fix-lint:
	yapf --in-place --parallel --recursive .
	isort --recursive --apply

download-dependencies:
	- rm -rf /tmp/dcos-docker
	curl -o /tmp/dcos_generate_config.sh $(ARTIFACT_URL)
	git clone -b $(DCOS_DOCKER_BRANCH) $(DCOS_DOCKER_REPOSITORY) /tmp/dcos-docker
