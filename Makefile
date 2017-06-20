SHELL := /bin/bash -euxo pipefail

ARTIFACT_URL := https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh

ARTIFACT_PATH := /tmp/dcos_generate_config.sh
EE_ARTIFACT_PATH := /tmp/dcos_generate_config.ee.sh

.PHONY: lint-python-only
lint-python-only:
	flake8 .
	isort --recursive --check-only
	yapf --diff --recursive src/ tests/ | \
	    python -c 'import sys; result = sys.stdin.read(); assert not result, result;'
	mypy src/ tests/
	pydocstyle
	pylint *.py src/dcos_e2e/ tests/

.PHONY: lint-docs
lint-docs:
	npm run lint-md
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
	npm run doctoc README.md CONTRIBUTING.md API.md --github --notitle
