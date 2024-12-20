"""
Tests for rewst remote agent
"""

import uuid
import pytest
from pytest_mock import MockerFixture
from rewst_remote_agent import main, signal_handler

# Constants
MODULE = "rewst_remote_agent"
ORG_ID = str(uuid.uuid4())


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_main(mocker: MockerFixture, platform: str) -> None:
    """
    Test for main()

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform tested.
    """
    mocker.patch("platform.system", return_value=platform)
    mocker.patch(f"{MODULE}.os_type", platform.lower())

    mocker.patch("sys.argv", [f"rewst_remote_agent_{ORG_ID}.win.exe"])
    mocked_load = mocker.patch(
        f"{MODULE}.load_configuration", return_value={"hello": "world"}
    )
    mocked_setup = mocker.patch(f"{MODULE}.setup_file_logging")
    mocker.patch(f"{MODULE}.iot_hub_connection_loop")

    if platform != "Windows":
        mocker.patch("asyncio.get_running_loop")

    assert await main() is None

    # Invalid args
    mocker.patch("sys.argv", [MODULE])
    assert await main() is None

    mocker.patch("sys.argv", [f"rewst_remote_agent_{ORG_ID}.win.exe"])

    # Raise exception on setup
    mocked_setup.side_effect = Exception
    assert await main() is None

    # Raise configuration error
    mocked_load.return_value = None
    assert await main() is None

    # Rase exception
    mocked_load.side_effect = Exception
    assert await main() is None


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_signal_handler(mocker: MockerFixture, platform: str) -> None:
    """
    Test for signal_handler()

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform tested.
    """
    mocker.patch("platform.system", return_value=platform)
    mocker.patch(f"{MODULE}.os_type", platform.lower())

    mocked_stop = mocker.MagicMock()
    mocker.patch(f"{MODULE}.stop_event", mocked_stop)

    signal_handler()

    mocked_stop.set.assert_called()
