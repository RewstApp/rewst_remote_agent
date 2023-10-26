#!/usr/bin/python3

import argparse
import asyncio
import httpx
import json
import logging
import os
import platform
import psutil
import re
import subprocess
import sys
# import traceback
from concurrent.futures import ThreadPoolExecutor
from azure.iot.device.aio import IoTHubDeviceClient
from service_manager import (
    get_executable_path,
    install_service,
    install_binaries,
    uninstall_service,
    start_service,
    stop_service,
    restart_service,
)
from config_module import (
    get_config_file_path,
    fetch_configuration,
    load_configuration,
    save_configuration
)

# Set the status update interval and get the operating system type
status_update_checkin_time = 600
os_type = platform.system().lower()
executor = ThreadPoolExecutor()

# Put Timestamps on logging entries
logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logging.info(f"Running on {os_type}")

# Function to send a status update to the IoT Hub
async def send_status_update():
    # Collect status data
    status_data = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent
    }
    # Create message object
    message_json = json.dumps(status_data)
    # Send message
    logging.info("Sending status update to IoT Hub...")
    await device_client.send_message(message_json)


# Function to construct a connection string from the configuration
def get_connection_string(config):
    conn_str = (
        f"HostName={config['azure_iot_hub_host']};"
        f"DeviceId={config['device_id']};"
        f"SharedAccessKey={config['shared_access_key']}"
    )
    return conn_str


# Configures listener for incoming messages
async def setup_message_handler(client):
    logging.info("Setting up message handler...")
    client.on_message_received = message_handler


# Handler function for messages received from the IoT Hub
async def message_handler(message):
    logging.info(f"Received message: {message.data}")
    try:
        message_data = json.loads(message.data)
        get_installation_info = message_data.get("get_installation")
        commands = message_data.get("commands")
        logging.info(commands)
        post_id = message_data.get("post_id")  # Get post_id, if present
        logging.info(post_id)
        interpreter_override = message_data.get("interpreter_override")  # Get custom interpreter, if present
        logging.info(interpreter_override)

        if post_id: # Post ID in message body
            post_path = post_id.replace(":", "/")
            post_url = f"https://{rewst_engine_host}/webhooks/custom/action/{post_path}"
            logging.info(f"Will POST results to {post_url}")

        if commands:  # Check if commands is not None
            logging.info("Received commands in message")
            await handle_commands(commands, post_url, interpreter_override)
        
        if get_installation_info:
            logging.info("Received request for installation paths")
            await get_installation(org_id, post_url)

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding message data as JSON: {e}")
        return  # Exit the function if the data can't be decoded as JSON
    

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


# Function to execute the list of commands
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
        script_block = f'{{{commands}}}'
        shell_command = f'{interpreter} -EncodedCommand "{commands}"'
    else:
        preamble = (f"post_url = '{post_url}'\n")
        commands = preamble + commands
        commands = commands.replace('"','\\"').replace("'","\\'").replace('\n',' ; ')
        shell_command = (f"base64 --decode '{commands}' | interpreter")

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

        # If the interpreter is not PowerShell, format the output as a JSON object and send it to the post_url
        if (post_url) and (interpreter != "powershell"):
            logging.info("Sending Results to Rewst via httpx.")
            response = httpx.post(post_url, json=message_data)
            logging.info(f"POST request status: {response.status_code}")
            if response.status_code != 200:
                logging.info(f"Error response: {response.text}")
    
        logging.info(f"Returning message_data back to calling function:\n{message_data}")
        return message_data

    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{shell_command}' failed with error code {e.returncode}")
        logging.error(f"Error output: {e.output}")
    except OSError as e:
        logging.error(f"OS error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")   


async def handle_commands(commands, post_url=None, interpreter_override=None):
    logging.info(f"Handling commands.")

    command_output = execute_commands(commands, post_url, interpreter_override)

    logging.info(f"returned from execute_commands: {command_output}")

    try:
        # Try to parse the output as JSON
        message_data = command_output
        logging.info(f"Loaded message_data: {message_data}")
    except json.JSONDecodeError as e:
        logging.info(f"Unable to decode command output as JSON: {e}, using string output instead")
        message_data = {"error": f"Unable to decode command output as JSON:: {e}", "output": command_output}
        logging.info(f"Ended up with message_data: {message_data}")
    except Exception as e:
        logging.error(f"An unexpected error occurred decoding JSON: {e}")    
    # Send the command output to IoT Hub
    message_json = json.dumps(message_data)
    try:
        await device_client.send_message(message_json)
        logging.info("Message sent to IoT Hub!")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")   


# Main async function
async def main(
    check_mode=False,
    config_file=None,
    config_url=None,
    config_secret=None,
    install_service_flag=False,
    uninstall_service_flag=False,
    start_service_flag=False,
    stop_service_flag=False,
    restart_service_flag=False,
):

    global rewst_engine_host
    global device_client
    global org_id

    try:
        if config_file:
            logging(f"Using config file {config_file}.")
            config_data = load_configuration(config_file=config_file)
        else:
            # Get Org ID for Config
            executable_path = os.path.basename(__file__)  # Gets the file name of the current script
            pattern = re.compile(r'rewst_remote_agent_(.+?)\.')
            match = pattern.search(executable_path)
            if match:
                org_id = match.group(1)
                logging.info(f"Found Org ID {org_id}")
                config_data = load_configuration(config_file)
            else:
                config_data = None

        if config_data is None and config_url:
            logging.info("Configuration file not found. Fetching configuration...")
            config_data = await fetch_configuration(config_url, config_secret)
            save_configuration(config_data)
            org_id = config_data['rewst_org_id']
            logging.info(f"Configuration saved to {get_config_file_path(org_id)}")
            install_binaries(org_id)
        elif config_data is None:
            logging.info("No configuration found and no config URL provided.")
            sys.exit(1)

        # Retrieve org_id from the configuration
        org_id = config_data['rewst_org_id']

        # Service management
        if install_service_flag and not config_url:
            install_service(org_id)
            start_service(org_id)  # Start the service after installation
        elif uninstall_service_flag:
            uninstall_service(org_id)
        elif start_service_flag:
            start_service(org_id)
        elif stop_service_flag:
            stop_service(org_id)
        elif restart_service_flag:
            restart_service(org_id)

        # Exit if any of the service management flags are set
        if any([
            install_service_flag,
            uninstall_service_flag,
            start_service_flag,
            stop_service_flag,
            restart_service_flag
        ]):
            sys.exit(0)

        # Connect to IoT Hub
        connection_string = get_connection_string(config_data)
        rewst_engine_host = config_data['rewst_engine_host']
        rewst_org_id = config_data['rewst_org_id']
        device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
        logging.info("Connecting to IoT Hub...")
        
        # Await client connection
        await device_client.connect()
        logging.info("Connected!")

        # Await incoming messages
        await setup_message_handler(device_client)

        stop_event = asyncio.Event()
    

        await stop_event.wait()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt. Shutting down...")
        await device_client.disconnect()



# Entry point of the script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--check', action='store_true', help='Run in check mode to test communication')
    parser.add_argument('--config-file', help='Path to the configuration file.')
    parser.add_argument('--config-url', help='URL to fetch the configuration from.')
    parser.add_argument('--config-secret', help='Secret to use when fetching the configuration.')
    parser.add_argument('--install-service', action='store_true', help='Install the service.')
    parser.add_argument('--uninstall-service', action='store_true', help='Uninstall the service.')
    parser.add_argument('--start-service', action='store_true', help='Start the service.')
    parser.add_argument('--restart-service', action='store_true', help='Restart the service.')
    parser.add_argument('--stop-service', action='store_true', help='Stop the service.')

    args = parser.parse_args()
    asyncio.run(main(
        check_mode=args.check,
        config_file=args.config_file,
        config_url=args.config_url,
        config_secret=args.config_secret,
        install_service_flag=args.install_service,
        uninstall_service_flag=args.uninstall_service,
        start_service_flag=args.start_service,
        stop_service_flag=args.stop_service,
        restart_service_flag=args.restart_service
    ))

