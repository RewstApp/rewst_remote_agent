import json
import logging
import httpx
import base64
import subprocess
import platform
from config_module import load_configuration


from error_handling import log_error

os_type = platform.system().lower()

async def send_message_to_iot_hub(client, message_data):
    # Assuming you have a function to send a message to IoT Hub.
    # Replace with your actual implementation if different.
    message_json = json.dumps(message_data)
    await client.send_message(message_json)

def execute_commands(commands, post_url=None, interpreter_override=None):
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
    if "powershell" in interpreter:
        shell_command = f'{interpreter} -EncodedCommand "{commands}"'
    else:
        decoded_commands = base64.b64decode(commands).decode('utf-16-le')
        preamble = f"post_url = '{post_url}'\n"
        combined_commands = preamble + decoded_commands
        re_encoded_commands = base64.b64encode(combined_commands.encode('utf-8'))
        shell_command = (f"base64 --decode '{re_encoded_commands}' | interpreter")

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
        log_error(f"An unexpected error occurred: {e}")
        message_data = {
            'output': '',
            'error': f"An unexpected error occurred: {e}"
        }

    if post_url:
        logging.info("Sending Results to Rewst via httpx.")
        response = httpx.post(post_url, json=message_data)
        logging.info(f"POST request status: {response.status_code}")
        if response.status_code != 200:
            logging.info(f"Error response: {response.text}")

    return message_data

async def handle_message(client, message, config_data):
    logging.info(f"Received IoT Hub message: {message.data}")
    try:
        message_data = json.loads(message.data)
        get_installation_info = message_data.get("get_installation")
        commands = message_data.get("commands")
        post_id = message_data.get("post_id")
        interpreter_override = message_data.get("interpreter_override")

        if post_id:
            post_path = post_id.replace(":", "/")
            rewst_engine_host = config_data["rewst_org_id"]
            post_url = f"https://{rewst_engine_host}/webhooks/custom/action/{post_path}"
            logging.info(f"Will POST results to {post_url}")

        if commands:
            logging.info("Received commands in message")
            command_output = execute_commands(commands, post_url, interpreter_override)
            await send_message_to_iot_hub(client, command_output)

        if get_installation_info:
            logging.info("Received request for installation paths")
            await get_installation(org_id, post_url)

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding message data as JSON: {e}")
    except Exception as e:
        log_error(f"An unexpected error occurred: {e}")

async def get_installation(org_id, post_url):
    executable_path = get_executable_path(org_id)
    config_file_path = get_config_file_path(org_id)
    
    paths_data = {
        "executable_path": executable_path,
        "config_file_path": config_file_path
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(post_url, json=paths_data)
        
    if response.status_code != 200:
        logging.error(f"Failed to post data: {response.status_code} - {response.text}")
