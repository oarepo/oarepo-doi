from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint

if TYPE_CHECKING:
    from flask import Flask
def create_doi_notifications(app: Flask) -> Blueprint:
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "oarepo_doi_notifications",
        __name__,
        template_folder=Path(__file__).parent.parent / "templates",
    )

    return blueprint