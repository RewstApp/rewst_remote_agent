"""
Tests for service management module
"""

import subprocess
import logging
import uuid
import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture
from service_module.service_management import (
    get_service_name,
    is_service_installed,
    is_service_running,
    install_service,
    uninstall_service,
    check_service_status,
    start_service,
    stop_service,
    restart_service
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
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_get_service_name(mocker: MockerFixture, platform: str) -> None:
    """
    Test get_service_name().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())

    assert get_service_name(ORG_ID) == SERVICE_NAME


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_is_service_installed(mocker: MockerFixture, platform: str) -> None:
    """
    Test is_service_installed().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
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
        mocker.patch("win32serviceutil.QueryServiceStatus",
                     side_effect=Exception)

    assert is_service_installed(ORG_ID) is False


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_is_service_running(mocker: MockerFixture, platform: str) -> None:
    """
    Test is_service_running().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("config_module.config_io.os_type", platform.lower())

    mocker.patch("psutil.process_iter", return_value=[])

    assert is_service_running(ORG_ID) is False

    extension = (
        "win.exe"
        if platform == "Windows"
        else "macos.bin" if platform == "Darwin" else "linux.bin"
    )
    executable_name = f"rewst_windows_service_{ORG_ID}.{extension}" if platform == "Windows" else f"rewst_remote_agent_{ORG_ID}.{extension}"
    mocker.patch(
        "psutil.process_iter",
        return_value=[mocker.MagicMock(info={"name": executable_name})],
    )

    assert is_service_running(ORG_ID) == executable_name


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_install_service(mocker: MockerFixture, platform: str) -> None:
    """
    Test install_service().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch(f"{MODULE}.is_service_installed", return_value=True)

    assert install_service(ORG_ID) is None

    mocker.patch(f"{MODULE}.is_service_installed", return_value=False)
    mocker.patch("subprocess.run")
    mocked_open = mocker.patch(f"{MODULE}.open", mocker.mock_open())

    assert install_service(ORG_ID) is None

    if platform != "Windows":
        mocked_open().write.assert_called()


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_uninstall_service(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test uninstall_service().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
        caplog (LogCaptureFixture): Fixture instance for detecting logs.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch(f"{MODULE}.stop_service")

    if platform == "Windows":
        mocker.patch("win32serviceutil.RemoveService")
    else:
        mocker.patch("subprocess.run")

    assert uninstall_service(ORG_ID) is None

    # Failed to stop service
    mocker.patch(f"{MODULE}.stop_service", side_effect=Exception("ERROR"))
    with caplog.at_level(logging.WARNING):
        assert uninstall_service(ORG_ID) is None

    assert "Unable to stop service: ERROR" in caplog.text

    # Failed to remove service for Windows
    if platform == "Windows":
        mocker.patch("win32serviceutil.RemoveService",
                     side_effect=Exception("ERROR"))

        with caplog.at_level(logging.WARNING):
            assert uninstall_service(ORG_ID) is None

        assert "Exception removing service: ERROR" in caplog.text


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin", "Unsupported"))
def test_check_service_status(mocker: MockerFixture, platform: str) -> None:
    """
    Test check_service_status().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())

    mocked_print = mocker.patch(f"{MODULE}.print")
    if platform == "Windows":
        mocker.patch("win32serviceutil.QueryServiceStatus")
    else:
        mocker.patch(
            "subprocess.run", return_value=mocker.MagicMock(stdout=SERVICE_NAME)
        )

    assert check_service_status(ORG_ID) is None

    mocked_print.assert_called()

    mocked_print = mocker.patch(f"{MODULE}.print")
    if platform == "Windows":
        mocker.patch("win32serviceutil.QueryServiceStatus")
    else:
        mocker.patch("subprocess.run",
                     return_value=mocker.MagicMock(stdout=""))

    assert check_service_status(ORG_ID) is None

    mocked_print.assert_called()

    # Failed to check status
    mocked_print = mocker.patch(f"{MODULE}.print")
    if platform == "Windows":
        mocker.patch("win32serviceutil.QueryServiceStatus",
                     side_effect=Exception)
    else:
        mocker.patch("subprocess.run", side_effect=Exception)

    assert check_service_status(ORG_ID) is None

    mocked_print.assert_called()

    # Failed to check status (subprocess.CalledProcessError)
    mocked_print = mocker.patch(f"{MODULE}.print")
    if platform == "Windows":
        mocker.patch("win32serviceutil.QueryServiceStatus",
                     side_effect=Exception)
    else:
        mocker.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                0, "TEST", output="TEST"),
        )

    assert check_service_status(ORG_ID) is None

    mocked_print.assert_called()


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_start_service(mocker: MockerFixture, platform: str) -> None:
    """
    Test start_service().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())

    if platform == "Windows":
        mocked_runner = mocker.patch("win32serviceutil.StartService")
    else:
        mocked_runner = mocker.patch("subprocess.run")

    assert start_service(ORG_ID) is None

    mocked_runner.assert_called()


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_stop_service(mocker: MockerFixture, platform: str) -> None:
    """
    Test stop_service().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    if platform == "Windows":
        mocked_runner = mocker.patch("win32serviceutil.QueryServiceStatus")
    else:
        mocked_runner = mocker.patch("subprocess.run")

    assert stop_service(ORG_ID) is None

    mocked_runner.assert_called()


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_restart_service(mocker: MockerFixture, platform: str) -> None:
    """
    Test restart_service().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): The current platform under test.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())

    mocked_stop = mocker.patch(f"{MODULE}.stop_service")
    mocked_start = mocker.patch(f"{MODULE}.start_service")

    assert restart_service(ORG_ID) is None

    mocked_stop.assert_called()
    mocked_start.assert_called()
