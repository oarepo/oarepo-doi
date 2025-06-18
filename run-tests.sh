#!/bin/bash

set -e
export PYTHONWARNINGS="ignore"
OAREPO_VERSION=${OAREPO_VERSION:-12}
export PIP_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple
export UV_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple
BUILDER_VENV=".venv-builder"
if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi

python3 -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install "oarepo[tests, rdm]==${OAREPO_VERSION}.*"
pip install -U setuptools pip wheel
pip install -U oarepo-model-builder \
               oarepo-model-builder-tests \
               oarepo-model-builder-requests \
               oarepo-model-builder-drafts \
               oarepo-model-builder-workflows \
               oarepo-model-builder-files \
               oarepo-model-builder-drafts-files

pip install -e ".[tests]"
if test -d ./thesis; then
	rm -rf ./thesis
fi

oarepo-compile-model ./tests/thesis.yaml --output-directory ./thesis -vvv

VENV_TESTS=".venv-tests"

if test -d $VENV_TESTS ; then
	rm -rf $VENV_TESTS
fi

python3 -m venv $VENV_TESTS
source $VENV_TESTS/bin/activate

pip install -U setuptools pip wheel

pip install "oarepo[tests, rdm]==${OAREPO_VERSION}.*"
pip install "./thesis[tests]"
pip install -e ".[tests]"


pytest tests -vvv