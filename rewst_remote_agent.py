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
import config_module
# import traceback
from concurrent.futures import ThreadPoolExecutor
from azure.iot.device.aio import IoTHubDeviceClient
from service_manager import (
    install_service,
    uninstall_service,
    start_service,
    stop_service,
    restart_service,
)
from config_module import fetch_configuration, load_configuration, save_configuration

# Set the status update interval and get the operating system type
status_update_checkin_time = 600
os_type = platform.system().lower()
executor = ThreadPoolExecutor()
logging.basicConfig(level=logging.INFO)
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
    logging.info("Status update sent!")


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
    logging.info("Message handler set up!")



# Handler function for messages received from the IoT Hub
async def message_handler(message):
    logging.info(f"Received message: {message.data}")
    try:
        message_data = json.loads(message.data)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding message data as JSON: {e}")
        return  # Exit the function if the data can't be decoded as JSON

    commands = message_data.get("commands")
    logging.info(commands)
    post_id = message_data.get("post_id")  # Get post_id, if present
    logging.info(post_id)
    interpreter_override = message_data.get("interpreter_override")  # Get custom interpreter, if present
    logging.info(interpreter_override)

    if post_id:
        post_path = post_id.replace(":", "/")
        post_url = f"https://{rewst_engine_host}/webhooks/custom/action/{post_path}"
        logging.info(f"Will POST results to {post_url}")

    if commands:  # Check if commands is not None
        logging.info("Received commands in message")
        loop = asyncio.get_running_loop()
        if loop is None:
            logging.error("No running event loop")
        else:
            # Schedule your synchronous function to run in the executor
            task = loop.run_in_executor(executor, handle_commands, commands, post_url, interpreter_override)
            # Await the completion of the task
            await task


# Function to execute the list of commands
def execute_commands(commands, post_url=None, interpreter_override=None):
    logging.info("In execute_commands")
    logging.info(f"post_url: {post_url}")


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
        logging.info(f"Adding preamble to handle secure posting back to rewst")
        preamble = (
            f"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12\n"
            f"$post_url = '{post_url}'\n"
        )
        # Prepend the preamble to the commands
        commands = preamble + commands

    # Create the command string based on the interpreter
    shell_command = f'{interpreter} -c "{commands}"'

    logging.info(f"Running Commands via:{shell_command}")

    # Execute the command
    try:
        logging.info("Opening Process")
        
        process = subprocess.Popen(
            shell_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        # Gather output
        stdout, stderr = process.communicate()
        logging.info("Process Completed.")

        message_data = {
            "output": stdout.strip(),
            "error": stderr.strip()
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

def handle_commands(commands, post_url=None, interpreter_override=None):    
    logging.info(f"Handling commands.")

    command_output = execute_commands(commands, post_url, interpreter_override)

    logging.info(f"returned from execute_commands: {command_output}")

    try:
        # Try to parse the output as JSON
        message_data = json.loads(command_output)
        logging.info(f"Loaded message_data: {message_data}")
    except json.JSONDecodeError as e:
        logging.info(f"Unable to decode command output as JSON: {e}, using string output instead")
        message_data = {"error": f"Unable to decode command output as JSON:: {e}", "output": command_output}
    
    # Send the command output to IoT Hub
    logging.info("dumping message_data to json")
    message_json = json.dumps(message_data)
    logging.info(f"Attempting to send message_json to iothub: {message_json}")
    try:
        device_client.send_message(message_json)
        logging.info("Message sent!")
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

    try:
        if config_file:
            logging(f"Using config file {config_file}.")
            config_data = load_configuration(config_file)
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
            logging.info(f"Configuration saved to {config_module.get_config_file_path(org_id)}")
            # install_service(org_id)  # Install the service if config_url is provided
            # logging.info("The service has been installed.")
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

