""" Version tracking module """

import subprocess

def get_poetry_version() -> str|None:
    """
    Get poetry version from poetry file.

    Returns:
        str|None: poetry version string if successful, otherwise None
    """
    try:
        version = subprocess.check_output(["poetry", "version", "--short"], text=True).strip()
        return version
    except subprocess.CalledProcessError:
        return None

__version__ = get_poetry_version()
