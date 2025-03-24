"""
Tests for connection management module
"""

import signal
import uuid
import asyncio
import subprocess
import json
from base64 import b64encode
import httpx
import pytest
from pytest_mock import MockerFixture
from iot_hub_module.connection_management import (
    ConnectionManager,
    iot_hub_connection_loop,
)

# Constants
MODULE = "iot_hub_module.connection_management"
ORG_ID = str(uuid.uuid4())
SERVICE_NAME = f"RewstRemoteAgent_{ORG_ID}"
EXECUTABLE_NAME = f"rewst_remote_agent_{ORG_ID}"
CONFIG_DATA = {
    "azure_iot_hub_host": "azure.com",
    "device_id": ORG_ID,
    "shared_access_key": ORG_ID,
    "rewst_engine_host": "engine.rewst.io",
    "rewst_org_id": ORG_ID,
}


@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_get_connection_string(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.get_connection_string().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocker.patch(f"{MODULE}.IoTHubDeviceClient.create_from_connection_string")

    conn = ConnectionManager(CONFIG_DATA)

    assert conn.get_connection_string() is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_connect(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.connect().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocked_client = mocker.AsyncMock()
    mocker.patch(
        f"{MODULE}.IoTHubDeviceClient.create_from_connection_string",
        return_value=mocked_client,
    )

    conn = ConnectionManager(CONFIG_DATA)

    assert await conn.connect() is None
    mocked_client.connect.assert_awaited()

    mocked_client.connect.side_effect = Exception
    assert await conn.connect() is None


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_disconnect(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.disconnect().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocked_client = mocker.AsyncMock()
    mocker.patch(
        f"{MODULE}.IoTHubDeviceClient.create_from_connection_string",
        return_value=mocked_client,
    )

    conn = ConnectionManager(CONFIG_DATA)

    assert await conn.disconnect() is None
    mocked_client.disconnect.assert_awaited()

    mocked_client.disconnect.side_effect = Exception
    assert await conn.disconnect() is None


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_send_message(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.send_message().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocked_client = mocker.AsyncMock()
    mocker.patch(
        f"{MODULE}.IoTHubDeviceClient.create_from_connection_string",
        return_value=mocked_client,
    )

    conn = ConnectionManager(CONFIG_DATA)
    message = {"HELLO": "WORLD"}

    assert await conn.send_message(message) is None
    mocked_client.send_message.assert_awaited_with(json.dumps(message))


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_set_message_handler(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.set_message_handler().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocked_client = mocker.AsyncMock()
    mocker.patch(
        f"{MODULE}.IoTHubDeviceClient.create_from_connection_string",
        return_value=mocked_client,
    )
    mocked_client.receive_message.side_effect = Exception

    conn = ConnectionManager(CONFIG_DATA)

    assert await conn.set_message_handler() is None


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_execute_commands(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.execute_commands().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocked_client = mocker.PropertyMock()
    mocker.patch(
        f"{MODULE}.IoTHubDeviceClient.create_from_connection_string",
        return_value=mocked_client,
    )
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.makedirs")

    mocker.patch("os.fsync")
    mocker.patch("tempfile.NamedTemporaryFile")

    # Set process.communicate output
    mocked_process = mocker.PropertyMock()
    mocked_process.communicate.return_value = ("", "")
    mocked_process.returncode = 1
    mocker.patch("subprocess.Popen", return_value=mocked_process)

    conn = ConnectionManager(CONFIG_DATA)
    test_command = "echo Hello World"
    test_command_b64 = b64encode(test_command.encode("utf-16-le"))
    assert await conn.execute_commands(test_command_b64) == {
        "output": "",
        "error": "Script execution failed with exit code 1. Error: ",
    }

    # Set process.communicate as success
    mocked_process.communicate.return_value = ("", None)
    mocked_process.returncode = 0
    assert await conn.execute_commands(test_command_b64) == {"output": "", "error": ""}

    # Raise error on process
    mocker.patch(
        "subprocess.Popen", side_effect=subprocess.CalledProcessError(0, "", "")
    )
    assert await conn.execute_commands(test_command_b64) == {
        "output": "",
        "error": "Command failed with error code 0: ",
    }

    mocker.patch("subprocess.Popen", side_effect=Exception)
    assert await conn.execute_commands(test_command_b64) == {
        "output": "",
        "error": "An unexpected error occurred: ",
    }

    # Send post url
    mocker.patch("httpx.AsyncClient")
    assert await conn.execute_commands(test_command_b64, "URL") == {
        "output": "",
        "error": "An unexpected error occurred: ",
    }

    # Trigger waiting for file to be deleted
    mocker.patch("os.path.exists", return_value=True)
    mocked_remove = mocker.patch("os.remove")
    assert await conn.execute_commands(test_command_b64) == {
        "output": "",
        "error": "An unexpected error occurred: ",
    }

    mocker.patch("os.path.exists", return_value=True)
    mocked_remove.side_effect = Exception
    assert await conn.execute_commands(test_command_b64) == {
        "output": "",
        "error": "An unexpected error occurred: ",
    }

    mocker.patch("os.path.exists", return_value=True)
    mocked_remove.side_effect = PermissionError

    async def toggle(time: float) -> None:
        await asyncio.sleep(time)
        mocked_remove.side_effect = Exception

    result, _ = await asyncio.gather(
        conn.execute_commands(test_command_b64), toggle(1.0)
    )
    assert result == {"output": "", "error": "An unexpected error occurred: "}


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_handle_message(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.handle_message().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocker.patch(f"{MODULE}.ConnectionManager.execute_commands")
    mocker.patch(f"{MODULE}.ConnectionManager.get_installation")

    test_command = "echo Hello World"
    test_command_b64 = b64encode(test_command.encode("utf-16-le"))
    conn = ConnectionManager(CONFIG_DATA)
    assert (
        await conn.handle_message(
            mocker.MagicMock(
                data=json.dumps(
                    {
                        "get_installation": True,
                        "commands": str(test_command_b64),
                        "post_id": ORG_ID,
                        "interpreter_override": "",
                    }
                )
            )
        )
        is None
    )

    # Failed execute commands
    mocker.patch(f"{MODULE}.ConnectionManager.execute_commands", side_effect=Exception)
    assert (
        await conn.handle_message(
            mocker.MagicMock(
                data=json.dumps(
                    {
                        "get_installation": True,
                        "commands": str(test_command_b64),
                        "post_id": ORG_ID,
                        "interpreter_override": "",
                    }
                )
            )
        )
        is None
    )

    # Failed get installation
    mocker.patch(f"{MODULE}.ConnectionManager.get_installation", side_effect=Exception)
    assert (
        await conn.handle_message(
            mocker.MagicMock(
                data=json.dumps(
                    {
                        "get_installation": True,
                        "commands": str(test_command_b64),
                        "post_id": ORG_ID,
                        "interpreter_override": "",
                    }
                )
            )
        )
        is None
    )

    # Missing post_id
    assert (
        await conn.handle_message(
            mocker.MagicMock(
                data=json.dumps(
                    {
                        "get_installation": True,
                        "commands": str(test_command_b64),
                        "post_id": None,
                        "interpreter_override": "",
                    }
                )
            )
        )
        is None
    )

    # Invalid data json format
    assert await conn.handle_message(mocker.MagicMock(data="Not a JSON")) is None

    # Generic exception raised
    mocker.patch("json.loads", side_effect=Exception)
    assert (
        await conn.handle_message(
            mocker.MagicMock(
                data=json.dumps(
                    {
                        "get_installation": True,
                        "commands": str(test_command_b64),
                        "post_id": None,
                        "interpreter_override": "",
                    }
                )
            )
        )
        is None
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_get_installation(mocker: MockerFixture, platform: str) -> None:
    """
    Test ConnectionManager.get_installation().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)

    conn = ConnectionManager(CONFIG_DATA)

    mocker.patch("httpx.AsyncClient", side_effect=Exception)
    assert await conn.get_installation("TEST_URL") is None

    mocker.patch("httpx.AsyncClient", side_effect=httpx.RequestError("HELLO"))
    assert await conn.get_installation("TEST_URL") is None

    mocker.patch(
        "httpx.AsyncClient",
        side_effect=httpx.HTTPStatusError(
            "HELLO",
            request=None,
            response=mocker.MagicMock(status_code=400, text="HELLO"),
        ),
    )
    assert await conn.get_installation("TEST_URL") is None

    mocker.patch("httpx.AsyncClient")
    assert await conn.get_installation("TEST_URL") is None


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
async def test_iot_hub_connection_loop(mocker: MockerFixture, platform: str) -> None:
    """
    Test iot_hub_connection_loop().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
        platform (str): Current platform parameter.
    """
    mocker.patch(f"{MODULE}.os_type", platform.lower())
    mocker.patch("platform.system", return_value=platform)
    mocked_client = mocker.AsyncMock()
    mocker.patch(
        f"{MODULE}.IoTHubDeviceClient.create_from_connection_string",
        return_value=mocked_client,
    )
    mocked_client.receive_message.side_effect = Exception

    stop_event = asyncio.Event()

    async def delayed_set(event: asyncio.Event, time: float) -> None:
        await asyncio.sleep(time)
        event.set()

    loop_result, _ = await asyncio.gather(
        iot_hub_connection_loop(CONFIG_DATA, stop_event), delayed_set(stop_event, 0.25)
    )

    assert loop_result is None

    # Trigger signal
    async def trigger_signal(time: float) -> None:
        await asyncio.sleep(time)
        signal.raise_signal(signal.SIGINT)

    result, _ = await asyncio.gather(
        iot_hub_connection_loop(CONFIG_DATA, stop_event), trigger_signal(0.5)
    )
    assert result is None
