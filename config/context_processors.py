from config import __version__


def project_version(request):
    """
    Expose the application version string to all templates.
    """
    return {
        "APP_VERSION": f"v{__version__}",
        "APP_VERSION_RAW": __version__,
    }

