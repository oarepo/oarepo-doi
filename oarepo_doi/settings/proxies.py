from flask import current_app

current_doi_settings = LocalProxy(  # type: ignore
    lambda: current_app.extensions["doi-settings"]
)
