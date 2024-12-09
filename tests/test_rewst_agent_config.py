"""
Tests for rewst agent config
"""

import logging
import uuid
import subprocess
import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture
from rewst_agent_config import (
    output_environment_info, is_valid_url, is_base64,
    remove_old_files, wait_for_files, install_and_start_service,
    check_service_status, end_program, main, start
)

# Constants
MODULE = "rewst_agent_config"
ORG_ID = str(uuid.uuid4())

@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_output_environment_info(
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
    mocker.patch("platform.release", return_value="1.0")
    mocker.patch("__version__.__version__", "1.0")

    with caplog.at_level(logging.INFO):
        assert output_environment_info() is None

        assert f"Running on {platform} 1.0" in caplog.text
        assert "Rewst Agent Configuration Tool v1.0" in caplog.text

def test_is_valid_url(mocker: MockerFixture, caplog: LogCaptureFixture) -> None:
    """
    Test is_valid_url().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    assert is_valid_url("https://rewst.io") is True

    with caplog.at_level(logging.ERROR):
        mocker.patch(f"{MODULE}.urlparse", side_effect=ValueError)
        assert is_valid_url("INVALID URL") is False
        assert "The provided string INVALID URL is not a valid URL" in caplog.text

def test_is_base64(mocker: MockerFixture) -> None:
    """
    Test is_base64().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    assert is_base64("!@#$%^") is False
    assert is_base64("1234567") is True

    mocker.patch("re.match", side_effect=Exception)
    assert is_base64("@#(!&la;dfa.sdf)") is False


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_remove_old_files(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test remove_old_files().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    mocker.patch("os.path.exists")
    mocker.patch("os.remove")
    mocked_rename = mocker.patch("os.rename")

    with caplog.at_level(logging.INFO):
        assert await remove_old_files(ORG_ID) is None
        assert caplog.text

    mocked_rename.side_effect = OSError

    with caplog.at_level(logging.ERROR):
        assert await remove_old_files(ORG_ID) is None
        assert caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_wait_for_files(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test wait_for_files().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    mocked_exists = mocker.patch("os.path.exists")
    mocker.patch("asyncio.sleep")

    with caplog.at_level(logging.INFO):
        assert await wait_for_files(ORG_ID) is True
        assert caplog.text

    mocked_exists.return_value = False
    with caplog.at_level(logging.WARNING):
        assert await wait_for_files(ORG_ID, 2) is False
        assert caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_install_and_start_service(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test install_and_start_service().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    mocked_subprocess = mocker.patch("asyncio.create_subprocess_exec")

    with caplog.at_level(logging.ERROR):
        assert await install_and_start_service(ORG_ID) is False
        assert caplog.text

    mocked_subprocess.return_value = mocker.AsyncMock()
    mocked_subprocess.return_value.communicate.return_value = (b"", b"")

    with caplog.at_level(logging.ERROR):
        assert await install_and_start_service(ORG_ID) is False
        assert caplog.text
    
    mocked_subprocess.return_value.returncode = 0
    mocked_run = mocker.patch("subprocess.run")

    with caplog.at_level(logging.INFO):
        assert await install_and_start_service(ORG_ID) is True
        assert caplog.text

    mocked_run.side_effect = subprocess.CalledProcessError(1, "")
    with caplog.at_level(logging.ERROR):
        assert await install_and_start_service(ORG_ID) is False 

@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_check_service_status(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test check_service_status().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    mocked_run = mocker.patch("subprocess.run", return_value=mocker.MagicMock())
    mocked_run.return_value.stdout = "running"

    with caplog.at_level(logging.INFO):
        assert await check_service_status(ORG_ID) is True
        assert caplog.text
    
    mocked_run.return_value.stdout = "error"

    with caplog.at_level(logging.INFO):
        assert await check_service_status(ORG_ID) is False
        assert caplog.text

    mocked_run.side_effect = subprocess.CalledProcessError(1, "error")

    with caplog.at_level(logging.ERROR):
        assert await check_service_status(ORG_ID) is False
        assert caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_end_program(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test end_program().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    mocked_exit = mocker.patch("sys.exit")

    with caplog.at_level(logging.INFO):
        assert end_program(42) is None
        mocked_exit.assert_called_with(42)
        assert caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_main(
    mocker: MockerFixture, platform: str, caplog: LogCaptureFixture
) -> None:
    """
    Test main().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
        caplog (LogCaptureFixture): Fixture instance for capturing logger.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    with pytest.raises(SystemExit):
        await main("THIS IS AN INVALID URL", "SECRET", ORG_ID)

    with pytest.raises(SystemExit):
        await main("https://rewst.io", "INVALID SECRET", ORG_ID)

    with pytest.raises(SystemExit):
        await main("https://rewst.io", "12345678", None)

    with pytest.raises(SystemExit):
        mocker.patch(f"{MODULE}.fetch_configuration", return_value=None)
        await main("https://rewst.io", "12345678", ORG_ID)

    with pytest.raises(SystemExit):
        mocker.patch(f"{MODULE}.fetch_configuration", return_value={"rewst_org_id": ORG_ID})
        mocker.patch(f"{MODULE}.save_configuration")
        mocker.patch(f"{MODULE}.ConnectionManager", return_value=mocker.AsyncMock())
        mocker.patch(f"{MODULE}.remove_old_files")
        mocker.patch(f"{MODULE}.wait_for_files")
        
        mocked_is_service_running = mocker.patch(f"{MODULE}.is_service_running", return_value=True)
        
        async def new_sleep(_: float) -> None:
            mocked_is_service_running.return_value = not mocked_is_service_running.return_value

        mocker.patch("asyncio.sleep", new=new_sleep)

        await main(f"https://rewst.io/config/{ORG_ID}", "12345678", ORG_ID)
    
    # Raise exception
    mocker.patch(f"{MODULE}.fetch_configuration", side_effect=Exception)
    await main(f"https://rewst.io/config/{ORG_ID}", "12345678", ORG_ID)

@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_start(
    mocker: MockerFixture, platform: str
) -> None:
    """
    Test start().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    mocker.patch(f"{MODULE}.main")
    mocker.patch("asyncio.run")

    with pytest.raises(SystemExit):
        start()

    mocker.patch("sys.argv", [MODULE, "--config-url", f"https://rewst.io/config/{ORG_ID}", "--config-secret", "12345678", "--org-id", ORG_ID])
    start()