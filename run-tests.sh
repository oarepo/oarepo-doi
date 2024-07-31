#!/bin/bash

set -e

OAREPO_VERSION=${OAREPO_VERSION:-12}

BUILDER_VENV=".venv-builder"
if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi

python3 -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install "oarepo[tests]==${OAREPO_VERSION}.*"
pip install -U setuptools pip wheel

pip install -e ".[tests]"

VENV_TESTS=".venv-tests"

if test -d ./thesis; then
	rm -rf ./thesis
fi
if test -d $VENV_TESTS ; then
	rm -rf $VENV_TESTS
fi
oarepo-compile-model ./tests/thesis.yaml --output-directory ./thesis -vvv

python3 -m venv $VENV_TESTS
source $VENV_TESTS/bin/activate

pip install -U setuptools pip wheel
pip install "oarepo[tests]==${OAREPO_VERSION}.*"
pip install "./thesis[tests]"
pip install -e ".[tests]"

pytest ./thesis/tests -vvv

pytest tests -vvv
