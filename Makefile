SHELL := /bin/bash -euxo pipefail

ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh

ARTIFACT_PATH := /tmp/dcos_generate_config.sh
EE_ARTIFACT_PATH := /tmp/dcos_generate_config.ee.sh

# Treat Sphinx warnings as errors
SPHINXOPTS := -W

# Run various linting tools.
.PHONY: lint
lint:
	check-manifest .
	doc8 .
	flake8 .
	isort --recursive --check-only
	mypy src/ tests/
	pip-extra-reqs src/
	pip-missing-reqs src/
	#pydocstyle
	pylint *.py src/ tests/
	pyroma .
	vulture . --min-confidence 100
	yapf --diff --recursive src/ tests/
	$(MAKE) -C docs linkcheck SPHINXOPTS=$(SPHINXOPTS)
	$(MAKE) -C docs spelling SPHINXOPTS=$(SPHINXOPTS)

# Attempt to clean leftovers by the test suite.
.PHONY: clean
clean:
	# Ignore errors in case there are no containers to remove.
	- docker stop $$(docker ps -a -q --filter="name=dcos-e2e") | :
	- docker rm --volumes $$(docker ps -a -q --filter="name=dcos-e2e") | :

# Fix some linting errors.
.PHONY: fix-lint
fix-lint:
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

.PHONY: docs
docs:
	make -C docs clean html SPHINXOPTS=$(SPHINXOPTS)

.PHONY: open-docs
open-docs:
	open docs/build/html/index.html

# DC/OS Docker is vendored in this repository using git subtree.
# To update DC/OS Docker, use the following command.
.PHONY: update-dcos-docker
update-dcos-docker:
	git subtree pull \
	    --prefix src/dcos_e2e/backends/_docker/dcos_docker \
	    --squash \
	    git@github.com:dcos/dcos-docker.git \
	    master
