SHELL := /bin/bash -euxo pipefail

ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh
DCOS_DOCKER_REPOSITORY := https://github.com/dcos/dcos-docker.git
DCOS_DOCKER_BRANCH := master

ARTIFACT_PATH := /tmp/dcos_generate_config.sh
EE_ARTIFACT_PATH := /tmp/dcos_generate_config.ee.sh
DCOS_DOCKER_CLONE_PATH := /tmp/dcos-docker

lint-python-only:
	flake8 .
	isort --recursive --check-only
	yapf --diff --parallel --recursive src/ tests/ | \
	    python -c 'import sys; result = sys.stdin.read(); assert not result, result;'
	mypy src/ tests/
	pydocstyle
	pylint *.py src/dcos_e2e/ tests/

lint-docs:
	npm run lint-md
	# Add ToCs and if there is a diff on Travis, error because we don't
	# want to ship docs without an up to date ToC
	if [ "${TRAVIS}" = "true" ] ; then \
	    npm run doctoc --github --notitle; \
	    git diff --exit-code ; \
	fi

# Run various linting tools.
lint: lint-python-only lint-docs
	# Don't lint travis.yml on Travis.
	if [ "${TRAVIS}" != "true" ] ; then travis lint --exit-code .travis.yml; fi


# Attempt to clean leftovers by the test suite.
clean:
	# Ignore errors in case there are no containers to remove.
	- docker stop $$(docker ps -a -q --filter="name=dcos-e2e") | :
	- docker rm --volumes $$(docker ps -a -q --filter="name=dcos-e2e") | :
	# We skip errors because this does not exist in legacy versions of
	# Docker
	- docker volume prune --force | :
	# On some platforms this requires `sudo`, e.g. Vagrant.
	# One some platforms, sudo requires a password.
	# Therefore try `sudo` and we try without `sudo`.
	- sudo -n rm -rf /tmp/dcos-docker-* | :
	- rm -rf /tmp/dcos-docker-* | :

# Fix some linting errors.
fix-lint: toc
	yapf --in-place --parallel --recursive .
	isort --recursive --apply

clean-dcos-docker:
	rm -rf $(DCOS_DOCKER_CLONE_PATH)

clean-artifacts:
	rm -rf $(ARTIFACT_PATH)
	rm -rf $(EE_ARTIFACT_PATH)

download-dcos-docker:
	git clone -b $(DCOS_DOCKER_BRANCH) $(DCOS_DOCKER_REPOSITORY) $(DCOS_DOCKER_CLONE_PATH)

download-artifacts:
	curl -o $(ARTIFACT_PATH) $(ARTIFACT_URL)
	if [ -n "$(EE_ARTIFACT_URL)" ]; then curl -o $(EE_ARTIFACT_PATH) $(EE_ARTIFACT_URL); fi

clean-dependencies: clean-dcos-docker clean-artifacts

download-dependencies: clean-dependencies download-artifacts download-dcos-docker

toc:
	npm run doctoc --github --notitle
