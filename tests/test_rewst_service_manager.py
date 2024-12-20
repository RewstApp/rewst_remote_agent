""" 
Tests for rewst service manager
"""
import uuid
import subprocess
import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture
from rewst_service_manager import main

# Constants
MODULE = "rewst_service_manager"
ORG_ID = str(uuid.uuid4())

@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_main(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test output_environment_info().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    with pytest.raises(SystemExit):
        mocker.patch("sys.argv", [MODULE])
        assert main() is None

    # Execute the install action
    mocker.patch(f"{MODULE}.install_service")
    mocker.patch(f"{MODULE}.start_service")
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID, "--install"])
    assert main() is None

    # Execute the uninstall action
    mocker.patch(f"{MODULE}.uninstall_service")
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID, "--uninstall"])
    assert main() is None

    # Execute the start action
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID, "--start"])
    assert main() is None

    # Execute the stop action
    mocker.patch(f"{MODULE}.stop_service")
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID, "--stop"])
    assert main() is None

    # Execute the restart action
    mocker.patch(f"{MODULE}.restart_service")
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID, "--restart"])
    assert main() is None

    # Execute the status action
    mocker.patch(f"{MODULE}.is_service_installed")
    mocker.patch(f"{MODULE}.check_service_status")
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID, "--status"])
    assert main() is None

    # No action specified 
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID])
    assert main() is None

    # Load the configuration
    mocker.patch(f"{MODULE}.load_configuration")
    mocker.patch("sys.argv", [MODULE, "--org-id", ORG_ID, "--config-file", "CONFIG FILE PATH"])
    assert main() is None