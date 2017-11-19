SHELL := /bin/bash -euxo pipefail

ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh

ARTIFACT_PATH := /tmp/dcos_generate_config.sh
EE_ARTIFACT_PATH := /tmp/dcos_generate_config.ee.sh

.PHONY: lint-python-only
lint-python-only:
	check-manifest .
	flake8 .
	isort --recursive --check-only
	mypy src/ tests/
	pydocstyle
	pylint *.py src/dcos_e2e/ tests/
	pyroma .
	yapf --diff --recursive src/ tests/

.PHONY: lint-docs
lint-docs:
	npm run lint-md *.md 2>&1 | \
	    python -c 'import sys; result = sys.stdin.read(); assert "warning" not in result, result'
	# Add ToCs and if there is a diff on Travis, error because we don't
	# want to ship docs without an up to date ToC
	if [ "${TRAVIS}" = "true" ] ; then \
	    $(MAKE) toc; \
	    git diff --exit-code ; \
	fi

# Run various linting tools.
.PHONY: lint
lint: lint-python-only lint-docs
	# Don't lint travis.yml on Travis.
	if [ "${TRAVIS}" != "true" ] ; then travis lint --exit-code .travis.yml; fi


# Attempt to clean leftovers by the test suite.
.PHONY: clean
clean:
	# Ignore errors in case there are no containers to remove.
	- docker stop $$(docker ps -a -q --filter="name=dcos-e2e") | :
	- docker rm --volumes $$(docker ps -a -q --filter="name=dcos-e2e") | :
	# We skip errors because this does not exist in legacy versions of
	# Docker
	- docker volume prune --force | :

# Fix some linting errors.
.PHONY: fix-lint
fix-lint: toc
	autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables .
	yapf --in-place --recursive .
	isort --recursive --apply

.PHONY: clean-artifacts
clean-artifacts:
	rm -rf $(ARTIFACT_PATH)
	rm -rf $(EE_ARTIFACT_PATH)

.PHONY: download-artifacts
download-artifacts:
	curl -o $(ARTIFACT_PATH) $(ARTIFACT_URL)
	if [ -n "$(EE_ARTIFACT_URL)" ]; then curl -o $(EE_ARTIFACT_PATH) $(EE_ARTIFACT_URL); fi

.PHONY: toc
toc:
	npm run doctoc *.md --github --notitle

# DC/OS Docker is vendored in this repository using git subtree.
# To update DC/OS Docker, use the following command.
.PHONY: update-dcos-docker
update-dcos-docker:
	git subtree pull \
	    --prefix src/dcos_e2e/backends/_docker/dcos_docker \
	    git@github.com:dcos/dcos-docker.git \
			--allow-unrelated-histories \
	    master
