import asyncio
import json
import logging
import httpx
import base64
import subprocess
import platform

from config_module.config_io import (
    get_config_file_path,
    get_agent_executable_path
)

os_type = platform.system().lower()


async def send_message_to_iot_hub(client, message_data):
    # Assuming you have a function to send a message to IoT Hub.
    # Replace with your actual implementation if different.
    message_json = json.dumps(message_data)
    await client.send_message(message_json)


# Configures listener for incoming messages
# async def setup_message_handler(client, config_data):
#     logging.info("Setting up message handler.")
#     try:
#         # client.on_message_received = handle_message(message, config_data)
#         client.on_message_received = handle_message(config_data, message)
#     except Exception as e:
#         logging.exception(f"An error occurred setting the message handler: {e}")
async def setup_message_handler(client, config_data):
    logging.info(f"Setting up message handler with config_data: {str(config_data)}")
    try:
        # Create a closure that captures config_data and passes it along with the message to handle_message
        client.on_message_received = lambda message: asyncio.create_task(handle_message(message, config_data))
    except Exception as e:
        logging.exception(f"An error occurred setting the message handler: {e}")


async def execute_commands(commands, post_url=None, interpreter_override=None):
    # Determine the interpreter based on the operating system
    if os_type == 'windows':
        default_interpreter = 'powershell'
    elif os_type == 'darwin':
        default_interpreter = '/bin/zsh'
    else:
        default_interpreter = '/bin/bash'

    # Use the default interpreter if an override isn't provided
    interpreter = interpreter_override or default_interpreter
    
    logging.info(f"Using interpreter: {interpreter}")

    # If PowerShell is the interpreter, update the commands to include the post_url variable
    # Typical Rewst workflows include Invoke-RestMethod to POST back to Rewst via this URL
    if "powershell" in interpreter:
        shell_command = f'{interpreter} -EncodedCommand "{commands}"'
    else:
        decoded_commands = base64.b64decode(commands).decode('utf-16-le')
        preamble = f"post_url = '{post_url}'\n"
        combined_commands = preamble + decoded_commands
        re_encoded_commands = base64.b64encode(combined_commands.encode('utf-8'))
        shell_command = f"base64 --decode '{re_encoded_commands}' | interpreter"

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

        message_data = {
            'output': stdout.strip(),
            'error': stderr.strip()
        }

    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{shell_command}' failed with error code {e.returncode}")
        logging.error(f"Error output: {e.output}")
        message_data = {
            'output': '',
            'error': f"Command failed with error code {e.returncode}: {e.output}"
        }
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        message_data = {
            'output': '',
            'error': f"An unexpected error occurred: {e}"
        }

    if post_url:
        logging.info("Sending Results to Rewst via httpx.")
        async with httpx.AsyncClient() as client:
            response = await client.post(post_url, json=message_data)
        logging.info(f"POST request status: {response.status_code}")
        if response.status_code != 200:
            logging.info(f"Error response: {response.text}")

    return message_data


async def handle_message(message, config_data):
    logging.info(f"Received IoT Hub message in handle_message: {message.data}")
    try:
        try:
            message_data = json.loads(message.data)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding message data as JSON: {e}")
            return
        get_installation_info = message_data.get("get_installation")
        commands = message_data.get("commands")
        post_id = message_data.get("post_id")
        interpreter_override = message_data.get("interpreter_override")
        org_id = config_data["rewst_org_id"]

        if post_id:
            post_path = post_id.replace(":", "/")
            rewst_engine_host = config_data["rewst_engine_host"]
            post_url = f"https://{rewst_engine_host}/webhooks/custom/action/{post_path}"
            logging.info(f"Will POST results to {post_url}")
        else:
            post_url = None

        if commands:
            logging.info("Received commands in message")
            try:
                await execute_commands(commands, post_id, interpreter_override)
            except Exception as e:
                logging.exception(f"Exception running commands: {e}")

        if get_installation_info:
            logging.info("Received request for installation paths")
            await get_installation(org_id, post_url)

    except json.JSONDecodeError as e:
        logging.exception(f"Error decoding message data as JSON: {e}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")


async def get_installation(org_id, post_url):
    executable_path = get_agent_executable_path(org_id)
    config_file_path = get_config_file_path(org_id)
    
    paths_data = {
        "executable_path": executable_path,
        "config_file_path": config_file_path
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(post_url, json=paths_data)
        
    if response.status_code != 200:
        logging.error(f"Failed to post data: {response.status_code} - {response.text}")