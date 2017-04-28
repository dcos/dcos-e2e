#!/usr/bin/env bash

# Source this file to give an environment for running end to end tests.
# This modifies the calling environment.
# Therefore it is recommended that this is used within a VM.
set -o
set -e

sudo yum install -y \
	make \
	wget \
	curl \
	llvm \
	tar \
	unzip \
	git \
	patch \
	gcc

curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash

echo "export PATH=\"~/.pyenv/bin:$PATH\"" >> ~/.bash_profile
echo "eval \"\$(pyenv init -)\"" >> ~/.bash_profile
echo "eval \"\$(pyenv virtualenv-init -)\"" >> ~/.bash_profile

source ~/.bash_profile

pyenv update

pyenv install --skip-existing 3.5.2

# || true because we want to continue whether or not there is an existing virtualenv
pyenv virtualenv 3.5.2 dcos || true
pyenv activate dcos

pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev-requirements.txt

set +o
set +e
