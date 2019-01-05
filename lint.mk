# Make commands for linting

SHELL := /bin/bash -euxo pipefail

.PHONY: yapf
yapf:
	yapf --diff --recursive .

.PHONY: fix-yapf
fix-yapf:
	yapf --in-place --recursive .

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

.PHONY: pylint
pylint:
	pylint *.py src/ tests/ admin/

.PHONY: pyroma
pyroma:
	pyroma --min 10 .

.PHONY: vulture
vulture:
	vulture --min-confidence 100 --exclude _vendor .

.PHONY: linkcheck
linkcheck:
	$(MAKE) -C docs/library linkcheck SPHINXOPTS=$(SPHINXOPTS)
	$(MAKE) -C docs/cli linkcheck SPHINXOPTS=$(SPHINXOPTS)

.PHONY: spelling
spelling:
	$(MAKE) -C docs/library spelling SPHINXOPTS=$(SPHINXOPTS)
	$(MAKE) -C docs/cli spelling SPHINXOPTS=$(SPHINXOPTS)

.PHONY: custom-linters
custom-linters:
	pytest -vvv -x admin/custom_linters.py

.PHONY: shellcheck
shellcheck:
	shellcheck --exclude SC2164,SC1091 admin/*.sh

.PHONY: autoflake
autoflake:
	autoflake \
	    --in-place \
	    --recursive \
	    --remove-all-unused-imports \
	    --remove-unused-variables \
	    --expand-star-imports \
	    --exclude _vendor,src/*/_version.py,versioneer.py,release \
	    .
