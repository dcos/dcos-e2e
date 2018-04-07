SHELL := /bin/bash -euxo pipefail

OSS_MASTER_ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh
OSS_1_9_ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/1.9/dcos_generate_config.sh
OSS_1_10_ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/1.10/dcos_generate_config.sh
OSS_1_11_ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/1.11/dcos_generate_config.sh

OSS_MASTER_ARTIFACT_PATH := /tmp/dcos_generate_config.sh
OSS_1_9_ARTIFACT_PATH := /tmp/dcos_generate_config_1_9.sh
OSS_1_10_ARTIFACT_PATH := /tmp/dcos_generate_config_1_10.sh
OSS_1_11_ARTIFACT_PATH := /tmp/dcos_generate_config_1_11.sh

EE_MASTER_ARTIFACT_PATH := /tmp/dcos_generate_config.ee.sh
EE_1_9_ARTIFACT_PATH := /tmp/dcos_generate_config_1_9.ee.sh
EE_1_10_ARTIFACT_PATH := /tmp/dcos_generate_config_1_10.ee.sh
EE_1_11_ARTIFACT_PATH := /tmp/dcos_generate_config_1_11.ee.sh

# Treat Sphinx warnings as errors
SPHINXOPTS := -W

.PHONY: yapf
yapf:
	yapf \
	    --diff \
	    --recursive \
	    --exclude src/dcos_e2e/_vendor \
	    --exclude src/dcos_e2e/_version.py \
	    --exclude release/ \
	    --exclude versioneer.py \
	    .

.PHONY: mypy
mypy:
	mypy *.py src/ tests/ admin/

.PHONY: check-manifest
check-manifest:
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
	pylint *.py src/ tests/ admin/

.PHONY: pyroma
pyroma:
	pyroma .

.PHONY: vulture
vulture:
	vulture --min-confidence 100 --exclude _vendor .

.PHONY: linkcheck
linkcheck:
	$(MAKE) -C docs linkcheck SPHINXOPTS=$(SPHINXOPTS)

.PHONY: spelling
spelling:
	$(MAKE) -C docs spelling SPHINXOPTS=$(SPHINXOPTS)


# Run various linting tools.
# We put each one in a different target so that we can run these in parallel with --jobs
.PHONY: lint
lint: \
    check-manifest \
    doc8 \
    flake8 \
    isort \
    linkcheck \
    mypy \
    pip-extra-reqs \
    pip-missing-reqs \
    pydocstyle \
    pylint \
    pyroma \
    spelling \
    vulture \
    yapf

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
	    --expand-star-imports \
	    --exclude src/dcos_e2e/_vendor,src/dcos_e2e/_version.py,versioneer.py,release \
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
	rm -rf $(OSS_MASTER_ARTIFACT_PATH)
	rm -rf $(EE_MASTER_ARTIFACT_PATH)

.PHONY: download-artifacts
download-artifacts:
	curl -o $(OSS_MASTER_ARTIFACT_PATH) $(OSS_MASTER_ARTIFACT_URL)
	curl -o $(OSS_1_9_ARTIFACT_PATH) $(OSS_1_9_ARTIFACT_URL)
	curl -o $(OSS_1_10_ARTIFACT_PATH) $(OSS_1_10_ARTIFACT_URL)
	curl -o $(OSS_1_11_ARTIFACT_PATH) $(OSS_1_11_ARTIFACT_URL)
	if [ -n "$(EE_MASTER_ARTIFACT_URL)" ]; then curl -o $(EE_MASTER_ARTIFACT_PATH) $(EE_MASTER_ARTIFACT_URL); fi
	if [ -n "$(EE_1_9_ARTIFACT_URL)" ]; then curl -o $(EE_1_9_ARTIFACT_PATH) $(EE_1_9_ARTIFACT_URL); fi
	if [ -n "$(EE_1_10_ARTIFACT_URL)" ]; then curl -o $(EE_1_10_ARTIFACT_PATH) $(EE_1_10_ARTIFACT_URL); fi
	if [ -n "$(EE_1_11_ARTIFACT_URL)" ]; then curl -o $(EE_1_11_ARTIFACT_PATH) $(EE_1_11_ARTIFACT_URL); fi

.PHONY: docs
docs:
	make -C docs clean html SPHINXOPTS=$(SPHINXOPTS)

.PHONY: open-docs
open-docs:
	xdg-open docs/build/html/index.html >/dev/null 2>&1 || \
	open docs/build/html/index.html >/dev/null 2>&1 || \
	echo "Requires 'xdg-open' or 'open' but neither is available."

# We pull Docker images before the tests start to catch any flakiness early.
# See https://jira.mesosphere.com/browse/DCOS_OSS-2120 for details of
# flakiness.
.PHONY: pull-images
pull-images:
	# These are the base images for operating systems used.
	docker pull ubuntu:xenial
	docker pull centos:7
	docker pull quay.io/shift/coreos:stable-1298.7.0
	# This is used by the ``dcos-docker doctor`` command.
	docker pull luca3m/sleep
