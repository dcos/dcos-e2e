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

# Fix some linting errors.
.PHONY: fix-lint
fix-lint:
	# Move imports to a single line so that autoflake can handle them.
	# See https://github.com/myint/autoflake/issues/8.
	# Then later we put them back.
	isort --force-single-line --recursive --apply
	$(MAKE) autoflake
	isort --recursive --apply
	$(MAKE) fix-yapf

.PHONY: docs-library
docs-library:
	make -C docs/library clean html SPHINXOPTS=$(SPHINXOPTS)

.PHONY: docs-cli
docs-cli:
	make -C docs/cli clean html SPHINXOPTS=$(SPHINXOPTS)

.PHONY: docs
docs: docs-library docs-cli

.PHONY: open-docs
open-docs:
	python -c 'import os, webbrowser; webbrowser.open("file://" + os.path.abspath("docs/library/build/html/index.html"))'
	python -c 'import os, webbrowser; webbrowser.open("file://" + os.path.abspath("docs/cli/build/html/index.html"))'

# We pull Docker images before the tests start to catch any flakiness early.
# See https://jira.d2iq.com/browse/DCOS_OSS-2120 for details of
# flakiness.
.PHONY: pull-images
pull-images:
	# These are the base images for operating systems used.
	docker pull ubuntu:xenial
	docker pull centos:7
	docker pull quay.io/shift/coreos:stable-1298.7.0
	# This is used by the ``minidcos docker doctor`` command.
	docker pull luca3m/sleep
	# This is used for testing installation.
	docker pull linuxbrew/linuxbrew
	# This is required for making Linux binaries
	docker pull python:3.7
