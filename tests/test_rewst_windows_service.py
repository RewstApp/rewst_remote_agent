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
    mocker.patch(f"{MODULE}.RewstWindowsService.stop_process")
    mocked_set_event = mocker.patch("win32event.SetEvent")

    args = [f"rewst_remote_agent_{ORG_ID}.win.exe"]

    mocker.patch("sys.argv", args)

    service = RewstWindowsService(args)

    assert service.SvcStop() is None
    mocked_set_event.assert_called()


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
    mocker.patch(f"{MODULE}.RewstWindowsService.start_process")

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
def test_start_process(mocker: MockerFixture) -> None:
    """
    Test for RewstWindowsService.start_process().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    RewstWindowsService.set_service_name(ORG_ID)

    mocker.patch("win32serviceutil.ServiceFramework")
    mocker.patch("subprocess.Popen")
    mocker.patch("time.sleep")

    args = [f"rewst_remote_agent_{ORG_ID}.win.exe"]
    mocker.patch("sys.argv", args)
    service = RewstWindowsService(args)

    # Exception raised
    assert service.start_process() is None

    # No exception
    mocker.patch(f"{MODULE}.is_checksum_valid", return_value=True)
    mocker.patch(
        "psutil.process_iter",
        return_value=(
            mocker.MagicMock(
                info={"name": f"rewst_remote_agent_{ORG_ID}.win", "pid": 1234}
            ),
        ),
    )
    assert service.start_process() is None


@pytest.mark.skipif(sys.platform != "win32", reason="Test only runs on Windows")
def test_stop_process(mocker: MockerFixture) -> None:
    """
    Test for RewstWindowsService.stop_process().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    RewstWindowsService.set_service_name(ORG_ID)

    mocker.patch("win32serviceutil.ServiceFramework")

    mocked_process_iter = mocker.patch("psutil.process_iter")
    mocked_process_iter.return_value = []

    mocked_process = mocker.patch("psutil.Process")
    mocked_process.return_value = mocker.MagicMock()

    args = [f"rewst_remote_agent_{ORG_ID}.win.exe"]
    mocker.patch("sys.argv", args)
    service = RewstWindowsService(args)

    # Kill from process_ids
    service.process_ids = [1234]
    assert service.stop_process() is None
    mocked_process.return_value.wait.assert_called()

    # Exception raised
    mocked_process.return_value.terminate.side_effect = Exception
    service.process_ids = [1234]
    assert service.stop_process() is None

    # psutil.NoSuchProcess raised
    mocked_process.return_value.terminate.side_effect = psutil.NoSuchProcess(1234)
    service.process_ids = [1234]
    assert service.stop_process() is None

    # psutil.TimeoutExpired
    mocked_process.return_value.terminate.side_effect = None
    mocked_process.return_value.wait.side_effect = psutil.TimeoutExpired(10)
    service.process_ids = [1234]
    assert service.stop_process() is None
    mocked_process.return_value.kill.assert_called()

    # Double tap
    mocked_proc = mocker.MagicMock(
        info={"name": f"rewst_remote_agent_{ORG_ID}.win.exe", "pid": 1234}
    )
    mocker.patch("psutil.process_iter", return_value=(mocked_proc,))
    assert service.stop_process() is None

    # Kill raises exception
    mocked_proc.kill.side_effect = Exception
    assert service.stop_process() is None


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
