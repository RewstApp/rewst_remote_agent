#!/usr/bin/python3

import argparse
import asyncio
import httpx
import json
import logging
import os
import platform
import psutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from azure.iot.device.aio import IoTHubDeviceClient

status_update_checkin_time = 600
os_type = platform.system()
executor = ThreadPoolExecutor()
logging.basicConfig(level=logging.INFO)

async def send_status_update():
    # Collect status data
    status_data = {
        "cpu_usage": psutil.cpu_percent(interval=1),  # CPU usage percentage
        "memory_usage": psutil.virtual_memory().percent  # Memory usage percentage
    }
    
    # Create message object
    message_json = json.dumps(status_data)
    
    # Send message
    print("Sending status update to IoT Hub...")
    await device_client.send_message(message_json)
    print("Status update sent!")


def load_config():
    try:
        with open('config.json') as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"Error: {e}")
        return None

    # Ensure all necessary configuration keys are present
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

def get_connection_string(config):
    # Build the connection string
    conn_str = (
        f"HostName={config['azure_iot_hub_host']};"
        f"DeviceId={config['device_id']};"
        f"SharedAccessKey={config['shared_access_key']}"
    )
    return conn_str


def message_handler(message):
    print(f"Received message: {message.data}")
    message_data = json.loads(message.data)
    if "commands" in message_data:
        commands = message_data["commands"]
        post_id = message_data["post_id"]  # Get post_id, if present
        print("Running commands")
        executor.submit(run_handle_commands, commands, post_id)  # Pass post_id to run_handle_commands


def run_handle_commands(commands, post_id=None):
    asyncio.run(handle_commands(commands, post_id, rewst_engine_host)) 

async def execute_commands(commands):
    # Create a temporary file to hold the commands
    fd, script_path = tempfile.mkstemp()
    print("Running Commands")
    if os_type == "Linux": 
        try:
            with os.fdopen(fd, 'w') as tmp:
                # Write commands to temporary file
                for command in commands:
                    print(command)
                    # Each command is followed by an echo statement to serve as a delimiter
                    tmp.write(f"{command}\necho '__COMMAND_SEPARATOR__'\n")

            # Execute temporary file as a script
            process = await asyncio.create_subprocess_exec(
                '/bin/bash', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Gather output
            stdout, stderr = await process.communicate()

            # The output will be in binary, so decode it to text
            stdout = stdout.decode('utf-8')

            # Split the output by the command separator to get individual command results
            command_results = stdout.strip().split('__COMMAND_SEPARATOR__\n')
            command_results = [result.strip() for result in command_results if result.strip()]
            
            return command_results
        finally:
            # Ensure temporary file is deleted
            os.remove(script_path)
    elif os_type == "Windows":
        try:
            for command in commands:
                result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
                print(result.stdout)  # or process result.stdout as needed
        finally:
            


async def handle_commands(commands, post_id=None, rewst_engine_host=None):
    command_results = await execute_commands(commands)
    message_data = {"command_results": command_results}
    message_json = json.dumps(message_data)
    await device_client.send_message(message_json)
    print("Message sent!")

    if post_id:
        # Replace ':' with '/' in post_id
        post_path = post_id.replace(":", "/")
        url = f"https://{rewst_engine_host}/webhooks/custom/action/{post_path}"
        print("Sending Results to Rewst.")
        # Send POST request with command results
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=message_data)
            print(f"POST request status: {response.status_code}")
            if response.status_code != 200:
                # Log error information if the request fails
                print(f"Error response: {response.text}")

async def main(check_mode=False):
    global rewst_engine_host
    config_data = load_config()
    if config_data is None:
        # Handle missing or invalid configuration
        exit(1)

    connection_string = get_connection_string(config_data)
    rewst_engine_host = config_data['rewst_engine_host']
    rewst_org_id = config_data['rewst_org_id']

    global device_client
    device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
    
    print("Connecting to IoT Hub...")
    await device_client.connect()
    print("Connected!")
    
    if check_mode:
        print("Check mode: Sending a test message...")
        e = None  # Define e before the try block
        try:
            # Send a test message
            await device_client.send_message(json.dumps({"test_message": "Test message from device"}))
            print("Check mode: Communication test successful. Test message sent.")
        except Exception as ex:
            e = ex  # Update e if an exception occurs
            print(f"Check mode: Communication test failed. Could not send test message: {e}")
        finally:
            # Disconnect from IoT Hub and exit
            await device_client.disconnect()
            exit(0 if not e else 1)  # Exit with code 0 on success, 1 on failure


    else:
        device_client.on_message_received = message_handler
    
        async def status_update_task():
            while True:
                await send_status_update()
                await asyncio.sleep(status_update_checkin_time)  # Send status update
        status_update_task = asyncio.create_task(status_update_task())

        stop_event = asyncio.Event()
        await stop_event.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--check', action='store_true', help='Run in check mode to test communication')
    args = parser.parse_args()
    
    asyncio.run(main(check_mode=args.check))
