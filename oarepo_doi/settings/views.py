def create_api_blueprint(app):
    """Create DOI settings blueprint."""
    blueprint = app.extensions[
        "doi-settings"
    ].doi_settings_resource.as_blueprint()

    return blueprint
