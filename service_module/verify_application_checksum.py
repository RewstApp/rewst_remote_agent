import hashlib
import httpx
import logging
import os
import re
from __version__ import __version__


def is_checksum_valid(executable_path):
    executable_name = os.path.basename(executable_path)
    checksum_file_name = f"{executable_name}.sha256"

    # Strip out the GUID if present in the filename
    checksum_file_name = re.sub(r'_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '',
                                checksum_file_name)

    github_checksum = fetch_checksum_from_github(checksum_file_name)
    local_checksum = calculate_local_file_checksum(executable_path)

    if github_checksum is None or local_checksum is None:
        logging.error("Failed to get one or both of the checksums.")
        return False

    return github_checksum == local_checksum


def get_release_info_by_tag(repo, tag):
    """
    Fetch release information from the GitHub repository for a specific tag.
    """
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def fetch_checksum_from_github(checksum_file_name):
    """
    Fetch the checksum from GitHub for a given file.
    """
    repo = "rewstapp/rewst_remote_agent"
    version_tag = f"v{__version__}"

    checksum_file_url = get_checksum_file_url(repo, version_tag, checksum_file_name)

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


def get_checksum_file_url(repo, tag, file_name):
    """
    Get the URL of the checksum file for a specific file in a specific release.
    """
    release_info = get_release_info_by_tag(repo, tag)
    for asset in release_info.get("assets", []):
        if asset["name"] == file_name:
            return asset["browser_download_url"]
    return None


def calculate_local_file_checksum(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.exception(f"Failed to calculate local file checksum: {e}")
        return None