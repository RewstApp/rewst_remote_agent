import httpx
from __version__ import __version__


def is_signature_valid(executable_path):
    repo = "rewstapp/rewst_remote_agent"
    version_tag = f"v{__version__}"
    checksum_file_name = f"{executable_path}.sha256"
    # WINTRUST_ACTION_GENERIC_VERIFY_V2 = "{00AAC56B-CD44-11d0-8CC2-00C04FC295EE}"
    try:

        return True
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False


def get_release_info_by_tag(repo, tag):
    """
    Fetch release information from the GitHub repository for a specific tag.
    """
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()

def get_checksum_file_url(repo, tag, file_name):
    """
    Get the URL of the checksum file for a specific file in a specific release.
    """
    release_info = get_release_info_by_tag(repo, tag)
    for asset in release_info.get("assets", []):
        if asset["name"] == file_name:
            return asset["browser_download_url"]
    return None