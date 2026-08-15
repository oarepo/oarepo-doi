
from __future__ import annotations

from importlib import util
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import Mock


def test_version():
    from oarepo_doi import __version__

    assert __version__
