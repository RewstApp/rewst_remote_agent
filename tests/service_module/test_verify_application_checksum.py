"""
Tests for verify application checksum module
"""

import uuid
from pytest_mock import MockerFixture
from service_module.verify_application_checksum import (
    is_checksum_valid,
    get_release_info_by_tag,
    fetch_checksum_from_github,
    get_checksum_file_url,
    calculate_local_file_checksum
)

# Constants
MODULE = "service_module.verify_application_checksum"
ORG_ID = str(uuid.uuid4())
SERVICE_NAME = f"RewstRemoteAgent_{ORG_ID}"
EXECUTABLE_NAME = f"rewst_remote_agent_{ORG_ID}"

def test_is_checksum_valid(mocker: MockerFixture) -> None:
    """
    Test is_checksum_valid().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """

    mocker.patch(f"{MODULE}.fetch_checksum_from_github", return_value="CHECKSUM1")
    mocker.patch(f"{MODULE}.calculate_local_file_checksum", return_value="CHECKSUM2")

    assert is_checksum_valid(EXECUTABLE_NAME) is False

    mocker.patch(f"{MODULE}.fetch_checksum_from_github", return_value="CHECKSUM1")
    mocker.patch(f"{MODULE}.calculate_local_file_checksum", return_value="CHECKSUM1")

    assert is_checksum_valid(EXECUTABLE_NAME) is True

    mocked_none_string = mocker.MagicMock()
    mocked_none_string.lower.return_value = None

    mocker.patch(f"{MODULE}.fetch_checksum_from_github", return_value=mocked_none_string)
    mocker.patch(f"{MODULE}.calculate_local_file_checksum", return_value="CHECKSUM1")

    assert is_checksum_valid(EXECUTABLE_NAME) is False

    mocker.patch(f"{MODULE}.fetch_checksum_from_github", return_value="CHECKSUM1")
    mocker.patch(f"{MODULE}.calculate_local_file_checksum", return_value=mocked_none_string)

    assert is_checksum_valid(EXECUTABLE_NAME) is False

def test_get_release_info_by_tag(mocker: MockerFixture) -> None:
    """
    Test get_release_info_by_tag().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocker.patch("httpx.Client")

    assert get_release_info_by_tag("TEST", "TEST") is not None

def test_fetch_checksum_from_github(mocker: MockerFixture) -> None:
    """
    Test fetch_checksum_from_github().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocker.patch(f"{MODULE}.get_checksum_file_url", return_value=None)

    assert fetch_checksum_from_github("TEST") is None

    mocker.patch(f"{MODULE}.get_checksum_file_url", return_value="TEST_URL")
    mocker.patch("httpx.Client")

    assert fetch_checksum_from_github("TEST") is None

    mocker.patch(f"{MODULE}.get_checksum_file_url", return_value="TEST_URL")
    mocker.patch("httpx.Client", side_effect=Exception)

    assert fetch_checksum_from_github("TEST") is None

    mocker.patch(f"{MODULE}.get_checksum_file_url", return_value="TEST_URL")
    
    mocked_response = mocker.PropertyMock()
    mocked_response.text = "Hash:CHECKSUM1"
    
    mocked_client = mocker.MagicMock()
    mocked_client.get.return_value = mocked_response

    mocked_instance = mocker.MagicMock()
    mocked_instance.__enter__.return_value = mocked_client
    mocked_instance.__exit__.return_value = None

    mocker.patch("httpx.Client", return_value=mocked_instance)

    assert fetch_checksum_from_github("TEST") is not None


def test_get_checksum_file_url(mocker: MockerFixture) -> None:
    """
    Test get_checksum_file_url().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocker.patch(f"{MODULE}.get_release_info_by_tag")
    
    assert get_checksum_file_url("rewstapp/rewst_remote_agent", "v1", "FILE") is None

    mocker.patch(f"{MODULE}.get_release_info_by_tag", return_value={
        "assets": [{
            "name": "FILE",
            "browser_download_url": "URL"
        }]
    })

    assert get_checksum_file_url("rewstapp/rewst_remote_agent", "v1", "FILE") == "URL"


def test_calculate_local_file_checksum(mocker: MockerFixture) -> None:
    """
    Test calculate_local_file_checksum().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocker.patch(f"{MODULE}.open", side_effect=Exception)

    assert calculate_local_file_checksum("FILE") is None

    mocker.patch(f"{MODULE}.open", mocker.mock_open(read_data=b"hello world"))

    assert calculate_local_file_checksum("FILE") is not None
