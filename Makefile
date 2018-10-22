SHELL := /bin/bash -euxo pipefail

# Treat Sphinx warnings as errors
SPHINXOPTS := -W

include lint.mk


.PHONY: lint
# We do not currently run pydocstyle as we have to ignore vendored items.
lint: \
    check-manifest \
    custom-linters \
    doc8 \
    flake8 \
    isort \
    linkcheck \
    mypy \
    pip-extra-reqs \
    pip-missing-reqs \
    pylint \
    pyroma \
    shellcheck \
    spelling \
    vulture \
    yapf

# Attempt to clean leftovers by the test suite.
.PHONY: clean
clean:
	# Ignore errors in case there are no containers to remove.
	- for sidecar in $$(dcos-docker list-loopback-sidecars); do dcos-docker destroy-loopback-sidecar $$sidecar; done
	- docker stop $$(docker ps -a -q --filter="name=dcos-e2e") | :
	- docker rm --volumes $$(docker ps -a -q --filter="name=dcos-e2e") | :
	- docker network rm $$(docker network ls -q --filter="name=dcos-e2e") | :

# Fix some linting errors.
.PHONY: fix-lint
fix-lint: autoflake fix-yapf
	isort --recursive --apply

.PHONY: docs
docs:
	make -C docs/library clean html SPHINXOPTS=$(SPHINXOPTS)
	make -C docs/cli clean html SPHINXOPTS=$(SPHINXOPTS)

.PHONY: open-docs
open-docs:
	xdg-open docs/library/build/html/index.html >/dev/null 2>&1 || \
	open docs/library/build/html/index.html >/dev/null 2>&1 || \
	echo "Requires 'xdg-open' or 'open' and the docs to be built."
	xdg-open docs/cli/build/html/index.html >/dev/null 2>&1 || \
	open docs/cli/build/html/index.html >/dev/null 2>&1 || \
	echo "Requires 'xdg-open' or 'open' and the docs to be built."

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
	# This is used for testing installation.
	docker pull linuxbrew/linuxbrew
	# This is required for making Linux binaries
	docker pull python:3.6
