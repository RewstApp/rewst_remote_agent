#!/usr/bin/python3

import argparse
import asyncio
import httpx
import json
import logging
import os
import platform
import psutil
import config_module
import traceback
from concurrent.futures import ThreadPoolExecutor
from azure.iot.device.aio import IoTHubDeviceClient

# Set the status update interval and get the operating system type
status_update_checkin_time = 600
os_type = platform.system()
executor = ThreadPoolExecutor()
logging.basicConfig(level=logging.INFO)

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

# Function to load configuration from a file
def load_config():
    try:
        with open('config.json') as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"Error: {e}")
        return None
    # Check for required keys in the configuration
    required_keys = [
        'azure_iot_hub_host',
        'device_id',
        'shared_access_key',
        'rewst_engine_host',
        'rewst_org_id'
    ]
    for key in required_keys:
        if key not in config:
            logging.error(f"Error: Missing '{key}' in configuration.")
            return None
    return config

# Function to construct a connection string from the configuration
def get_connection_string(config):
    conn_str = (
        f"HostName={config['azure_iot_hub_host']};"
        f"DeviceId={config['device_id']};"
        f"SharedAccessKey={config['shared_access_key']}"
    )
    return conn_str

# Handler function for messages received from the IoT Hub
def message_handler(message):
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
            task = loop.create_task(run_handle_commands(commands, post_url, interpreter_override))
            task.add_done_callback(error_callback)
    else:
        logging.info("No commands to run")


# Function to handle the execution of commands
async def run_handle_commands(commands, post_url=None, interpreter_override=None):
    logging.info("In run_handle_commands")
    await handle_commands(commands, post_url, interpreter_override)

def error_callback(future):
    exc = future.exception()
    if exc:
        logging.error(f"Exception in run_handle_commands: {exc}")
        logging.error(traceback.format_exc())



# Async function to execute the list of commands
async def execute_commands(commands, post_url=None, interpreter_override=None):
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
        preamble = (
            f"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12\n"
            f"$post_url = '{post_url}'\n"
        )
        # Prepend the preamble to the commands
        commands = preamble + commands

    # Create the command string based on the interpreter
    command = f'{interpreter} -c "{commands}"'

    # Execute the command
    try:
        logging.info("Executing Commands")
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Gather output
        stdout, stderr = await process.communicate()
            # Decode output from binary to text
        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        # If the interpreter is not PowerShell, format the output as a JSON object and send it to the post_url
        if (post_url) and ("powershell" not in interpreter):
            message_data = {
            "output": stdout.strip(),
            "error": stderr.strip()
        }
            logging.info("Sending Results to Rewst via httpx.")
            async with httpx.AsyncClient() as client:
                response = await client.post(post_url, json=message_data)
                logging.info(f"POST request status: {response.status_code}")
                if response.status_code != 200:
                    # Log error information if the request fails
                    logging.info(f"Error response: {response.text}")
            return None  # return None or an empty string if you don't want to return anything
        else:
            return stdout.strip()  # returning the PowerShell command output or other output you want to return
        
    except Exception as e:
        logging.error(f"Exception in execute_commands: {e}")


# Async function to handle the execution of commands and send the output to IoT Hub
async def handle_commands(commands, post_url=None, interpreter_override=None):    
    logging.info(f"Handling commands: {commands}")

    # Execute the commands
    logging.info(f"Executing commands: {commands}")

    command_output = await execute_commands(commands, post_url, interpreter_override)
    logging.info("completed")
    try:
        # Try to parse the output as JSON
        message_data = json.loads(command_output)
    except json.JSONDecodeError as e:
        logging.info(f"Error decoding command output as JSON: {e}, using string output instead")
        message_data = {"error": f"Error decoding command output as JSON: {e}", "output": command_output}
    # Send the command output to IoT Hub
    message_json = json.dumps(message_data)
    await device_client.send_message(message_json)
    logging.info("Message sent!")

# Main async function
async def main(check_mode=False, config_url=None, config_secret=None):

    global rewst_engine_host
    config_data = load_config()
    if config_data is None and config_url:
        logging.info("Configuration file not found. Fetching configuration...")
        config_data = await config_module.fetch_configuration(config_url, config_secret)
        config_module.save_configuration(config_data)
        logging.info(f"Configuration saved to config.json")
    elif config_data is None:
        logging.info("No configuration found and no config URL provided.")
        exit(1)


    # Connect to IoT Hub
    connection_string = get_connection_string(config_data)
    rewst_engine_host = config_data['rewst_engine_host']
    rewst_org_id = config_data['rewst_org_id']
    global device_client
    device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
    logging.info("Connecting to IoT Hub...")
    await device_client.connect()
    logging.info("Connected!")
    if check_mode:
        # Check mode for testing communication
        logging.info("Check mode: Sending a test message...")
        e = None
        try:
            await device_client.send_message(json.dumps({"test_message": "Test message from device"}))
            logging.info("Check mode: Communication test successful. Test message sent.")
        except Exception as ex:
            e = ex
            logging.info(f"Check mode: Communication test failed. Could not send test message: {e}")
        finally:
            await device_client.disconnect()
            exit(0 if not e else 1)
    else:
        # Set the message handler and start the status update task
        device_client.on_message_received = message_handler
        async def status_update_task():
            while True:
                await send_status_update()
                await asyncio.sleep(status_update_checkin_time)
        status_update_task = asyncio.create_task(status_update_task())
        stop_event = asyncio.Event()
        await stop_event.wait()

# Entry point of the script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--check', action='store_true', help='Run in check mode to test communication')
    parser.add_argument('--config-url', help='URL to fetch the configuration from.')
    parser.add_argument('--config-secret', help='Secret to use when fetching the configuration.')
    args = parser.parse_args()
    asyncio.run(main(check_mode=args.check, config_url=args.config_url, config_secret=args.config_secret)) 