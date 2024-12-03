"""
Tests for service management module
"""

import logging
import uuid
from pytest import mark
from pytest_mock import MockerFixture
from service_module.service_management import (
    get_service_name, is_service_installed
)
from rewst_windows_service import RewstWindowsService

# Constants
MODULE = "service_module.service_management"
ORG_ID = str(uuid.uuid4())
SERVICE_NAME = f"RewstRemoteAgent_{ORG_ID}"
EXECUTABLE_NAME = f"rewst_remote_agent_{ORG_ID}"

# Module setup
RewstWindowsService.set_service_name(ORG_ID)

# Tests
@mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_get_service_name(mocker: MockerFixture, platform: str) -> None:
    """
    Test get_service_name().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())

    assert get_service_name(ORG_ID) == SERVICE_NAME


@mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_is_service_installed(mocker: MockerFixture, platform: str) -> None:
    """
    Test is_service_installed().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    
    if platform != "Windows":
        mocker.patch("os.path.exists", return_value=True)
    else:
        mocker.patch("win32serviceutil.QueryServiceStatus")

    assert is_service_installed(ORG_ID) is True

    if platform != "Windows":
        mocker.patch("os.path.exists", return_value=False)
    else:
        mocker.patch("win32serviceutil.QueryServiceStatus", side_effect=Exception)

    assert is_service_installed(ORG_ID) is False

