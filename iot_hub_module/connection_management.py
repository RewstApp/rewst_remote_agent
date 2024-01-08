import asyncio
import base64
import httpx
import json
import logging
import os
import platform
import signal
import tempfile
import subprocess
from azure.iot.device.aio import IoTHubDeviceClient

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
    def __init__(self, config_data):
        self.config_data = config_data
        self.connection_string = self.get_connection_string()
        self.os_type = platform.system().lower()
        self.client = IoTHubDeviceClient.create_from_connection_string(self.connection_string)

    def get_connection_string(self):
        conn_str = (
            f"HostName={self.config_data['azure_iot_hub_host']};"
            f"DeviceId={self.config_data['device_id']};"
            f"SharedAccessKey={self.config_data['shared_access_key']}"
        )
        return conn_str

    async def connect(self):
        try:
            await self.client.connect()
        except Exception as e:
            logging.exception(f"Exception in connection to the IoT Hub: {e}")

    async def disconnect(self):
        try:
            await self.client.disconnect()
        except Exception as e:
            logging.exception(f"Exception in disconnecting from the IoT Hub: {e}")

    async def send_message(self, message_data):
        message_json = json.dumps(message_data)
        await self.client.send_message(message_json)

    async def set_message_handler(self):
        try:
            self.client.on_message_received = self.handle_message
        except Exception as e:
            logging.exception(f"Exception in handling message: {e}")

    async def execute_commands(self, commands, post_url=None, interpreter_override=None):
        interpreter = interpreter_override or self.get_default_interpreter()
        logging.info(f"Using interpreter: {interpreter}")
        output_message_data = None

        # Write commands to a temporary file
        script_suffix = ".ps1" if "powershell" in interpreter.lower() else ".sh"
        tmp_dir = None
        if os_type == "windows":
            config_dir = site_config_dir()
            scripts_dir = os.path.join(config_dir, "\\RewstRemoteAgent\\scripts")
            # scripts_dir = "C:\\Scripts"
            if not os.path.exists(scripts_dir):
                os.makedirs(scripts_dir)
            tmp_dir = scripts_dir
        with tempfile.NamedTemporaryFile(delete=False, suffix=script_suffix,
                                         mode="w", dir=tmp_dir) as temp_file:
            if "powershell" in interpreter.lower():
                # If PowerShell is used, decode the commands
                decoded_commands = base64.b64decode(commands).decode('utf-16-le')
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

        logging.info(f"Wrote commands to temp file {temp_file_path}")

        # Construct the shell command to execute the temp file
        if "powershell" in interpreter.lower() or "pwsh" in interpreter.lower():
            shell_command = f'{interpreter} -File "{temp_file_path}"'
        else:
            shell_command = f'{interpreter} "{temp_file_path}"'

        try:
            # Execute the command
            logging.info(f"Running process via commandline: {shell_command}")
            process = subprocess.Popen(
                shell_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            logging.info(f"Command completed with exit code {exit_code}")

            if exit_code != 0 or stderr:
                # Log and print error details
                error_message = f"Script execution failed with exit code {exit_code}. Error: {stderr}"
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
            logging.error(f"Command '{shell_command}' failed with error code {e.returncode}")
            logging.error(f"Error output: {e.output}")
            output_message_data = {
                'output': '',
                'error': f"Command failed with error code {e.returncode}: {e.output}"
            }

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
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
                    logging.error(f"Error deleting temporary file: {e}")
                    break  # If a different error occurs, break out of the loop

        if post_url and output_message_data:
            logging.info("Sending Results to Rewst via httpx.")
            async with httpx.AsyncClient() as client:
                response = await client.post(post_url, json=output_message_data)
            logging.info(f"POST request status: {response.status_code}")
            if response.status_code != 200:
                logging.error(f"Error response: {response.text}")

        return output_message_data

    async def handle_message(self, message):

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
                post_url = f"https://{rewst_engine_host}/webhooks/custom/action/{post_path}"
                logging.info(f"Will POST results to {post_url}")
            else:
                post_url = None

            if commands:
                logging.info("Received commands in message")
                try:
                    await self.execute_commands(commands, post_url, interpreter_override)
                except Exception as e:
                    logging.exception(f"Exception running commands: {e}")

            if get_installation_info:
                logging.info("Received request for installation paths")
                try:
                    await self.get_installation(post_url)
                except Exception as e:
                    logging.exception(f"Exception getting installation info: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding message data as JSON: {e}")
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")

    async def get_installation(self, post_url):
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
            logging.error(f"Error response {e.response.status_code} while posting to {post_url}: {e.response.text}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while posting to {post_url}: {e}")

    def get_default_interpreter(self):
        if self.os_type == 'windows':
            return 'powershell'
        elif self.os_type == 'darwin':
            return '/bin/zsh'
        else:
            return '/bin/bash'


async def iot_hub_connection_loop(config_data, stop_event):
    stop_event = asyncio.Event()

    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}. Initiating graceful shutdown.")
        stop_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Instantiate ConnectionManager
        connection_manager = ConnectionManager(config_data)

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
        while not stop_event.is_set():
            await asyncio.sleep(1)

        # Before disconnecting, update Device Twin reported properties to 'offline'
        logging.info("Updating device status to offline...")
        twin_patch = {"connectivity": {"status": "offline"}}
        await connection_manager.client.patch_twin_reported_properties(twin_patch)

        await connection_manager.disconnect()

    except Exception as e:
        logging.exception(f"Exception Caught during IoT Hub Loop: {str(e)}")


