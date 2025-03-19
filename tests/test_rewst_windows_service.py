"""
Tests for rewst windows service
"""

import sys
import logging
import uuid
import pytest
import psutil
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture
from rewst_windows_service import RewstWindowsService, main

# Constants
MODULE = "rewst_windows_service"
ORG_ID = str(uuid.uuid4())


@pytest.mark.skipif(sys.platform != "win32", reason="Test only runs on Windows")
def test_set_service_name() -> None:
    """
    Test for RewstWindowsService.set_service_name().
    """
    RewstWindowsService.set_service_name(ORG_ID)

    assert RewstWindowsService.get_service_name() == f"RewstRemoteAgent_{ORG_ID}"
    assert (
        RewstWindowsService.get_service_display_name()
        == f"Rewst Agent Service for Org {ORG_ID}"
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Test only runs on Windows")
def test_init(mocker: MockerFixture, caplog: LogCaptureFixture) -> None:
    """
    Test for RewstWindowsService.__init__().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    RewstWindowsService.set_service_name(ORG_ID)

    mocker.patch("win32serviceutil.ServiceFramework")
    mocker.patch("win32event.CreateEvent")

    with caplog.at_level(logging.INFO):
        args = [f"rewst_remote_agent_{ORG_ID}.win.exe"]

        mocker.patch("sys.argv", args)

        service = RewstWindowsService(args)

        assert service.org_id == ORG_ID
        assert caplog.text

    with caplog.at_level(logging.WARNING):
        args = [MODULE]

        mocker.patch("sys.argv", args)

        service = RewstWindowsService(args)

        assert service.org_id == False
        assert caplog.text


@pytest.mark.skipif(sys.platform != "win32", reason="Test only runs on Windows")
def test_svc_stop(mocker: MockerFixture) -> None:
    """
    Test for RewstWindowsService.SvcStop().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    RewstWindowsService.set_service_name(ORG_ID)

    mocker.patch("win32serviceutil.ServiceFramework")
    mocker.patch(f"{MODULE}.RewstWindowsService.ReportServiceStatus")

    args = [f"rewst_remote_agent_{ORG_ID}.win.exe"]

    mocker.patch("sys.argv", args)

    service = RewstWindowsService(args)

    assert service.SvcStop() is None


@pytest.mark.skipif(sys.platform != "win32", reason="Test only runs on Windows")
def test_svc_do_run(mocker: MockerFixture) -> None:
    """
    Test for RewstWindowsService.SvcDoRun().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    RewstWindowsService.set_service_name(ORG_ID)

    mocker.patch("win32serviceutil.ServiceFramework")
    mocker.patch(f"{MODULE}.RewstWindowsService.ReportServiceStatus")

    mocked_wait = mocker.patch("win32event.WaitForSingleObject", return_value=1)

    args = [f"rewst_remote_agent_{ORG_ID}.win.exe"]
    mocker.patch("sys.argv", args)
    service = RewstWindowsService(args)

    service.process = mocker.MagicMock()

    def toggle_wait(_) -> None:
        mocked_wait.return_value -= 1

    mocker.patch("logging.warning", new=toggle_wait)

    assert service.SvcDoRun() is None

@pytest.mark.skipif(sys.platform != "win32", reason="Test only runs on Windows")
def test_main(mocker: MockerFixture) -> None:
    """
    Test for main().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    RewstWindowsService.set_service_name(ORG_ID)

    mocker.patch("sys.argv", [f"rewst_remote_agent_{ORG_ID}.win.exe"])

    mocked_init = mocker.patch("servicemanager.Initialize")
    mocked_prepare = mocker.patch("servicemanager.PrepareToHostSingle")
    mocked_start = mocker.patch("servicemanager.StartServiceCtrlDispatcher")

    assert main() is None
    mocked_init.assert_called()
    mocked_prepare.assert_called()
    mocked_start.assert_called()

    # Org id not found
    mocker.patch("sys.argv", [MODULE])
    assert main() is None

    # Execute as a command line executable
    mocked_handle = mocker.patch("win32serviceutil.HandleCommandLine")
    mocker.patch("sys.argv", [f"rewst_remote_agent_{ORG_ID}.win.exe", "arg0"])

    assert main() is None
    mocked_handle.assert_called()
