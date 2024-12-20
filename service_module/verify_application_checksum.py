""" Module for verifying the checksum of the application binary. """

from typing import AnyStr, Any

import hashlib
import logging
import os
import re
import httpx

from __version__ import __version__


def is_checksum_valid(executable_path: os.PathLike[AnyStr]) -> bool:
    """
    Validates the checksum of an executable.

    Args:
        executable_path (os.PathLike[AnyStr]): The pathname of the executable.

    Returns:
        bool: True if checksum is valid, otherwise False.
    """
    executable_name = os.path.basename(executable_path)
    checksum_file_name = f"{executable_name}.sha256"

    # Strip out the GUID if present in the filename
    checksum_file_name = re.sub(r'_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '',
                                checksum_file_name)

    github_checksum = fetch_checksum_from_github(checksum_file_name).lower()
    logging.info(f"GH Checksum: {github_checksum}")
    local_checksum = calculate_local_file_checksum(executable_path).lower()
    logging.info(f"Local Checksum: {local_checksum}")

    if github_checksum is None or local_checksum is None:
        logging.error("Failed to get one or both of the checksums.")
        return False

    return github_checksum == local_checksum


def get_release_info_by_tag(repo: str, tag: str) -> Any:
    """
    Fetch release information from the GitHub repository for a specific tag.

    Args:
        repo (str): Name of the repository.
        tag (str): Tag of the repository.

    Returns:
        Any: Release details in JSON format.
    """

    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def fetch_checksum_from_github(checksum_file_name: str) -> str | None:
    """
    Fetch the checksum from GitHub for a given file. 
    Returns None if checksum file does not exist.

    Args:
        checksum_file_name (str): Checksum file name.

    Returns:
        str|None: Checksum of the file if specified, otherwise None.
    """

    repo = "rewstapp/rewst_remote_agent"
    version_tag = f"v{__version__}"

    checksum_file_url = get_checksum_file_url(
        repo, version_tag, checksum_file_name)

    if not checksum_file_url:
        logging.error(f"Checksum file URL not found for {checksum_file_name}")
        return None

    try:
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(checksum_file_url)
            response.raise_for_status()
            checksum_data = response.text.strip()

            # Parse the checksum data
            for line in checksum_data.split('\n'):
                if line.startswith('Hash'):
                    return line.split(':')[1].strip()
    except Exception as e:
        logging.exception(f"Failed to fetch checksum from GitHub: {e}")
        return None


def get_checksum_file_url(repo: str, tag: str, file_name: str) -> str | None:
    """
    Get the URL of the checksum file for a specific file in a specific release.
    Returns None if URL is not specified in the asset list.

    Args:
        repo (str): Name of the repository.
        tag (str): Tag of the repoistory.
        file_name (str): File name of the executable.

    Returns:
        str|None: Download URL if specified in the assets, otherwise None.
    """

    release_info = get_release_info_by_tag(repo, tag)
    for asset in release_info.get("assets", []):
        if asset["name"] == file_name:
            return asset["browser_download_url"]
    return None


def calculate_local_file_checksum(file_path: str) -> str | None:
    """
    Calculate the checksum of a local file path.
    Returns None on error.

    Args:
        file_path (str): File path of a local file.

    Returns:
        str|None: Checksum of the file or None if failed.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.exception(f"Failed to calculate local file checksum: {e}")
        return None
