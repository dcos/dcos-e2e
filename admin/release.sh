# Perform a release.
# See the release process documentation for details.
cd $(mktemp -d)
cd dcos-e2e
git clone git@github.com:mesosphere/dcos-e2e.git
virtualenv -p python3 release
source release/bin/activate
pip install --editable .[dev]
python admin/prepare_release.py
