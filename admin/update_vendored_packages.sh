#!/usr/bin/env bash

# Update vendored packages.

# ``python-vendorize`` has problems with pip 10.0.0
OLD_PIP=$(python -c 'import pkg_resources; print(pkg_resources.get_distribution("pip").parsed_version.public)')
git rm -rf src/dcos_e2e/_vendor/
rm -rf src/dcos_e2e/_vendor
pip install pip==9.0.1
python admin/update_vendored_packages.py
pip install pip=="$OLD_PIP"
git add src/dcos_e2e/_vendor
git commit -m "Update vendored packages"
