""" Module for defining class and functions to manage connections. """

from typing import Dict, Any

import asyncio
import base64
import json
import os
import subprocess
import logging
import platform
import signal
import tempfile
import httpx

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device.iothub.models import Message
from azure.iot.device.exceptions import ConnectionFailedError, ConnectionDroppedError

from platformdirs import (
    site_config_dir
)
from config_module.config_io import (
    get_config_file_path,
    get_agent_executable_path,
    get_service_executable_path,
    get_service_manager_path
)
from config_module.host_info import build_host_tags

# Set up logging
logging.basicConfig(level=logging.INFO)

os_type = platform.system().lower()


class ConnectionManager:
    """
    Manages the connection between the agent and IoT Hub.
    """

    def __init__(self, config_data: Dict[str, Any], connection_retry: bool = True) -> None:
        """Construcs a new connection manager instance

        Args:
            config_data (Dict[str, Any]): Configuration data of the connection.
            connection_retry (bool): Automatically retry connection.
        """
        self.config_data = config_data
        self.connection_string = self.get_connection_string()
        self.os_type = platform.system().lower()

        self.__connection_retry = connection_retry

    def __make_client(self, websockets: bool = False) -> IoTHubDeviceClient:
        """
        Make an IotHub Device client instance.

        Args:
            websockets (bool, optional): Use webosocket connection to IoTHub. Defaults to False.

        Returns:
            IoTHubDeviceClient: Client instance.
        """
        return IoTHubDeviceClient.create_from_connection_string(
            self.connection_string,
            websockets=websockets,
            connection_retry=self.__connection_retry
        )

    def get_connection_string(self) -> str:
        """
        Get the connection string used to connect to the IoT Hub.

        Returns:
            str: Connection string to the IoT Hub.
        """
        conn_str = (
            f"HostName={self.config_data['azure_iot_hub_host']};"
            f"DeviceId={self.config_data['device_id']};"
            f"SharedAccessKey={self.config_data['shared_access_key']}"
        )
        return conn_str

    async def connect_using_websockets(self) -> None:
        """
        Modify the connection to use websockets and reconnect
        """
        try:
            logging.info("Connecting over websockets...")
            self.client = self.__make_client(True)
            await self.client.connect()
        except Exception as e:
            logging.exception("Exception in connection to the IoT Hub: %s", e)

    async def connect(self) -> None:
        """
        Connect the agent service to the IoT Hub.
        """
        try:
            self.client = self.__make_client(False)
            await self.client.connect()
        except (ConnectionFailedError, ConnectionDroppedError):
            await self.connect_using_websockets()
        except Exception as e:
            logging.exception("Exception in connection to the IoT Hub: %s", e)

    async def disconnect(self) -> None:
        """
        Disconnect the agent service from the IoT Hub.
        """
        try:
            await self.client.disconnect()
        except Exception as e:
            logging.exception(
                "Exception in disconnecting from the IoT Hub: %s", e)

    async def send_message(self, message_data: Dict[str, Any]) -> None:
        """
        Send a message to the IoT Hub.

        Args:
            message_data (Dict[str, Any]): Message data in JSON format.
        """
        message_json = json.dumps(message_data)
        await self.client.send_message(message_json)

    async def set_message_handler(self) -> None:
        """
        Sets the event handler for income messages from the Iot Hub.
        """
        self.client.on_message_received = self.handle_message

    async def execute_commands(self, commands: bytes, post_url: str = None, interpreter_override: str = None) -> Dict[str, str]:
        """
        Execute commands on the machine using the specified interpreter and send back result via post_url.

        Args:
            commands (str): Base64 encoded list of commands.
            post_url (str, optional): Post back URL to send the stdout and stderr results of the commands after execution. Defaults to None.
            interpreter_override (str, optional): Interpreter name to use in executing the commands. Defaults to None.

        Returns:
            Dict[str, str]: Output message in JSON format sent to the post_url.
        """
        interpreter = interpreter_override or self.get_default_interpreter()
        logging.info("Using interpreter: %s", interpreter)
        output_message_data = None

        # Write commands to a temporary file
        script_suffix = ".ps1" if "powershell" in interpreter.lower() else ".sh"
        tmp_dir = None
        if os_type == "windows":
            config_dir = site_config_dir()
            scripts_dir = os.path.join(
                config_dir, "\\RewstRemoteAgent\\scripts")
            # scripts_dir = "C:\\Scripts"
            if not os.path.exists(scripts_dir):
                os.makedirs(scripts_dir)
            tmp_dir = scripts_dir
        with tempfile.NamedTemporaryFile(delete=False, suffix=script_suffix,
                                         mode="w", dir=tmp_dir) as temp_file:
            if "powershell" in interpreter.lower():
                # If PowerShell is used, decode the commands
                decoded_commands = base64.b64decode(
                    commands).decode('utf-16-le')
                # Ensure TLS 1.2 configuration is set at the beginning of the command
                tls_command = "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12"
                if tls_command not in decoded_commands:
                    decoded_commands = tls_command + "\n" + decoded_commands
            else:
                # For other interpreters, you might want to handle encoding differently
                decoded_commands = base64.b64decode(commands).decode('utf-8')

            # logging.info(f"Decoded Commands:\n{decoded_commands}")
            temp_file.write(decoded_commands)
            temp_file.flush()  # Explicitly flush the file buffer
            os.fsync(temp_file.fileno())  # Ensures all data is written to disk
            temp_file_path = temp_file.name

        logging.info("Wrote commands to temp file %s", temp_file_path)

        # Construct the shell command to execute the temp file
        if "powershell" in interpreter.lower() or "pwsh" in interpreter.lower():
            shell_command = f'{interpreter} -File "{temp_file_path}"'
        else:
            shell_command = f'{interpreter} "{temp_file_path}"'

        try:
            # Execute the command
            logging.info("Running process via commandline: %s", shell_command)
            process = subprocess.Popen(
                shell_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            logging.info("Command completed with exit code %d", exit_code)

            if exit_code != 0 or stderr:
                # Log and print error details
                error_message = f"Script execution failed with exit code {
                    exit_code}. Error: {stderr}"
                logging.error(error_message)
                print(error_message)  # Print to console
                output_message_data = {
                    'output': stdout,
                    'error': error_message
                }
            else:
                output_message_data = {
                    'output': stdout,
                    'error': ''
                }

        except subprocess.CalledProcessError as e:
            logging.error(
                "Command '%s' failed with error code %d", shell_command, e.returncode)
            logging.error("Error output: %s", e.output)
            output_message_data = {
                'output': '',
                'error': f"Command failed with error code {e.returncode}: {e.output}"
            }

        except Exception as e:
            logging.error("An unexpected error occurred: %s", e)
            output_message_data = {
                'output': '',
                'error': f"An unexpected error occurred: {e}"
            }

        finally:
            # Loop to wait until the file can be deleted
            while True:
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    break  # If successful, break out of the loop
                except PermissionError:
                    await asyncio.sleep(1)
                except Exception as e:
                    logging.error("Error deleting temporary file: %s", e)
                    break  # If a different error occurs, break out of the loop

        if post_url and output_message_data:
            logging.info("Sending Results to Rewst via httpx.")
            async with httpx.AsyncClient() as client:
                response = await client.post(post_url, json=output_message_data)
            logging.info("POST request status: %d", response.status_code)
            if response.status_code != 200:
                if response.status_code == 400 and ("fulfilled" in response.text.lower()):
                    logging.info("Webhook POST fulfilled by Script")
                else:
                    logging.error("Error response: %s", response.text)

        return output_message_data

    async def handle_message(self, message: Message) -> None:
        """Handle incoming message event from the IoT Hub.

        Args:
            message (Message): Message instance from the IoT Hub.
        """
        logging.info("Received IoT Hub message in handle_message.")
        try:
            message_data = json.loads(message.data)
            get_installation_info = message_data.get("get_installation")
            commands = message_data.get("commands")
            post_id = message_data.get("post_id")
            interpreter_override = message_data.get("interpreter_override")

            if post_id:
                post_path = post_id.replace(":", "/")
                rewst_engine_host = self.config_data["rewst_engine_host"]
                post_url = f"https://{
                    rewst_engine_host}/webhooks/custom/action/{post_path}"
                logging.info("Will POST results to %s", post_url)
            else:
                post_url = None

            if commands:
                logging.info("Received commands in message")
                try:
                    await self.execute_commands(commands, post_url, interpreter_override)
                except Exception as e:
                    logging.exception("Exception running commands: %s", e)

            if get_installation_info:
                logging.info("Received request for installation paths")
                try:
                    await self.get_installation(post_url)
                except Exception as e:
                    logging.exception(
                        "Exception getting installation info: %s", e)
        except json.JSONDecodeError as e:
            logging.error("Error decoding message data as JSON: %s", e)
        except Exception as e:
            logging.exception("An unexpected error occurred: %s", e)

    async def get_installation(self, post_url: str) -> None:
        """Send installation data of the service to the Rewst platform. The post_url
        is an ephemeral link generated by the Rewst platform.

        Args:
            post_url (str): Post back link to send the installation data to.
        """
        org_id = self.config_data['rewst_org_id']
        service_executable_path = get_service_executable_path(org_id)
        agent_executable_path = get_agent_executable_path(org_id)
        service_manager_path = get_service_manager_path(org_id)
        config_file_path = get_config_file_path(org_id)

        paths_data = {
            "service_executable_path": service_executable_path,
            "agent_executable_path": agent_executable_path,
            "config_file_path": config_file_path,
            "service_manager_path": service_manager_path,
            "tags": build_host_tags(org_id)
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(post_url, json=paths_data)
                response.raise_for_status()

        except httpx.RequestError as e:
            logging.error(f"Request to {post_url} failed: {e}")
        except httpx.HTTPStatusError as e:
            logging.error(
                f"Error response {e.response.status_code} while posting to {post_url}: {e.response.text}")
        except Exception as e:
            logging.error(
                f"An unexpected error occurred while posting to {post_url}: {e}")

    def get_default_interpreter(self) -> str:
        """Get the default interpreter depending on the platform's OS type.

        Returns:
            str: Interpreter executable path.
        """
        if self.os_type == 'windows':
            return 'powershell'
        elif self.os_type == 'darwin':
            return '/bin/zsh'
        else:
            return '/bin/bash'


async def iot_hub_connection_loop(config_data: Dict[str, Any], stop_event: asyncio.Event = asyncio.Event(), use_signals: bool = True) -> None:
    """Connect to the IoT Hub and wait for a stop event to close the loop.

    Args:
        config_data (Dict[str, Any]): Configuration data of the agent service.
        stop_event (asyncio.Event): Stop event instance.
        use_signals (bool): Use signal handlers to monitor the stop event.s
    """
    if use_signals:
        def signal_handler(signum, frame):
            logging.info(
                f"Received signal {signum}. Initiating graceful shutdown.")
            stop_event.set()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    # Set connection constants
    connection_retry_interval = 10

    while not stop_event.is_set():
        try:
            # Instantiate ConnectionManager
            connection_manager = ConnectionManager(config_data, False)

            # Connect to IoT Hub
            logging.info("Connecting to IoT Hub...")
            await connection_manager.connect()

            # Update Device Twin reported properties to 'online'
            logging.info("Updating device status to online...")
            twin_patch = {"connectivity": {"status": "online"}}
            await connection_manager.client.patch_twin_reported_properties(twin_patch)

            # Set Message Handler
            logging.info("Setting up message handler...")
            await connection_manager.set_message_handler()

            # Use an asyncio.Event to exit the loop when the service stops
            while not stop_event.is_set() and connection_manager.client.connected:
                await asyncio.sleep(1)

            if connection_manager.client.connected:
                # Before disconnecting, update Device Twin reported properties to 'offline'
                logging.info("Updating device status to offline...")
                twin_patch = {"connectivity": {"status": "offline"}}
                await connection_manager.client.patch_twin_reported_properties(twin_patch)

                await connection_manager.disconnect()
                return
            else:
                logging.info("Client disconnected")

        except Exception as e:
            logging.exception(
                f"Exception Caught during IoT Hub Loop: {str(e)}")

        # Reconnect
        logging.info("Reconnecting in %d seconds...",
                     connection_retry_interval)

        await asyncio.sleep(connection_retry_interval)
