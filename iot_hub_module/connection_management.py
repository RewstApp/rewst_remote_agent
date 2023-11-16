import asyncio
import base64
import httpx
import json
import logging
import platform
import subprocess
from azure.iot.device.aio import IoTHubDeviceClient

from config_module.config_io import (
    get_config_file_path,
    get_agent_executable_path
)

# Set up logging
logging.basicConfig(level=logging.INFO)


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

        # If PowerShell is the interpreter, update the commands to include the post_url variable
        # Typical Rewst workflows include Invoke-RestMethod to POST back to Rewst via this URL
        if "powershell" in interpreter.lower():
            shell_command = f'{interpreter} -EncodedCommand "{commands}"'
        else:
            decoded_commands = base64.b64decode(commands).decode('utf-16-le')
            preamble = f"post_url = '{post_url}'\n"
            combined_commands = preamble + decoded_commands
            re_encoded_commands = base64.b64encode(combined_commands.encode('utf-8'))
            shell_command = f"echo {re_encoded_commands} | base64 --decode | {interpreter}"

        # Execute the command
        try:
            process = subprocess.Popen(
                shell_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            # Gather output
            stdout, stderr = process.communicate()
            exit_code = process.returncode  # Get the exit code
            logging.info(f"Process Completed with exit code {exit_code}.")
            logging.info(f"Standard Output: {stdout}")
            if stderr:
                logging.error(f"Standard Error: {stderr}")

            output_message_data = {
                'output': stdout.strip(),
                'error': stderr.strip(),
                'exit_code': exit_code
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

        if post_url:
            logging.info("Sending Results to Rewst via httpx.")
            async with httpx.AsyncClient() as client:
                response = await client.post(post_url, json=output_message_data)
            logging.info(f"POST request status: {response.status_code}")
            if response.status_code != 200:
                logging.error(f"Error response: {response.text}")

        return output_message_data

    async def handle_message(self, message):

        logging.info(f"Received IoT Hub message in handle_message: {message.data}")
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
        org_id = self.config_data['org_id']
        executable_path = get_agent_executable_path(org_id)
        config_file_path = get_config_file_path(org_id)

        paths_data = {
            "executable_path": executable_path,
            "config_file_path": config_file_path
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

