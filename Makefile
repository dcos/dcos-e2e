SHELL := /bin/bash -euxo pipefail

ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh

ARTIFACT_PATH := /tmp/dcos_generate_config.sh
EE_ARTIFACT_PATH := /tmp/dcos_generate_config.ee.sh

# Treat Sphinx warnings as errors
SPHINXOPTS := -W

.PHONY: yapf
yapf:
	yapf \
	    --diff \
	    --recursive \
	    --exclude src/dcos_e2e/_vendor \
	    --exclude src/dcos_e2e/_version.py \
	    --exclude versioneer.py \
	    .

.PHONY: mypy
mypy:
	python admin/run_mypy.py

.PHONY: check-manifest
check-makifest:
	check-manifest .

.PHONY: doc8
doc8:
	doc8 .

.PHONY: flake8
flake8:
	flake8 .

.PHONY: isort
isort:
	isort --recursive --check-only

.PHONY: pip-extra-reqs
pip-extra-reqs:
	pip-extra-reqs src/

.PHONY: pip-missing-reqs
pip-missing-reqs:
	pip-missing-reqs src/

.PHONY: pydocstyle
pydocstyle:
	pydocstyle

.PHONY: pylint
pylint:
	pylint *.py src/ tests/

.PHONY: pyroma
pyroma:
	pyroma .

.PHONY: vulture
vulture:
	vulture . --min-confidence 100

.PHONY: linkcheck
linkcheck:
	$(MAKE) -C docs linkcheck SPHINXOPTS=$(SPHINXOPTS)

.PHONY: spelling
spelling:
	$(MAKE) -C docs spelling SPHINXOPTS=$(SPHINXOPTS)


# Run various linting tools.
.PHONY: lint
lint: mypy yapf check-manifest doc8 flake8 isort pip-extra-reqs pip-missing-reqs pydocstyle pylint pyroma vulture linkcheck spelling

# Attempt to clean leftovers by the test suite.
.PHONY: clean
clean:
	# Ignore errors in case there are no containers to remove.
	- docker stop $$(docker ps -a -q --filter="name=dcos-e2e") | :
	- docker rm --volumes $$(docker ps -a -q --filter="name=dcos-e2e") | :

# Fix some linting errors.
.PHONY: fix-lint
fix-lint:
	autoflake \
	    --in-place \
	    --recursive \
	    --remove-all-unused-imports \
	    --remove-unused-variables \
	    --exclude src/dcos_e2e/_vendor,src/dcos_e2e/_version.py,versioneer.py \
	    .
	yapf \
	    --in-place \
	    --recursive \
	    --exclude src/dcos_e2e/_vendor \
	    --exclude src/dcos_e2e/_version.py \
	    --exclude versioneer.py \
	    .
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

.PHONY: update-homebrew
update-homebrew:
	python admin/homebrew_recipe.py > dcosdocker.rb

# DC/OS Docker is vendored in this repository using git subtree.
# To update DC/OS Docker, use the following command.
.PHONY: update-dcos-docker
update-dcos-docker:
	git subtree pull \
	    --prefix src/dcos_e2e/backends/_docker/dcos_docker \
	    --squash \
	    git@github.com:dcos/dcos-docker.git \
	    master
