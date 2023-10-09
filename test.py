#!/usr/bin/python3

import argparse
import asyncio
import httpx
import json
import logging
import os
import platform
import psutil
from concurrent.futures import ThreadPoolExecutor
from azure.iot.device.aio import IoTHubDeviceClient

status_update_checkin_time = 600
os_type = platform.system()
executor = ThreadPoolExecutor()
logging.basicConfig(level=logging.INFO)

async def send_status_update():
    status_data = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent
    }
    message_json = json.dumps(status_data)
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
        post_id = message_data.get("post_id")
        interpreter_delimiter = message_data.get("interpreter_delimiter", "\n")
        print("Running commands")
        executor.submit(run_handle_commands, commands, post_id, None, None, interpreter_delimiter)

def run_handle_commands(commands, post_id=None, rewst_engine_host=None, interpreter=None, interpreter_delimiter="\n"):
    asyncio.run(handle_commands(commands, post_id, rewst_engine_host, interpreter, interpreter_delimiter))

async def execute_commands(commands, post_url=None, interpreter_override=None, interpreter_delimiter="\n"):
    if os_type == 'windows':
        default_interpreter = 'powershell'
    elif os_type == 'darwin':
        default_interpreter = '/bin/zsh'
    else:
        default_interpreter = '/bin/bash'
    interpreter = interpreter_override or default_interpreter
    all_commands = interpreter_delimiter.join(commands)
    command = f'{interpreter} -c "{all_commands}"'
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    stdout = stdout.decode('utf-8')
    return stdout.strip()

async def handle_commands(commands, post_id=None, rewst_engine_host=None, interpreter_override=None, interpreter_delimiter="\n"):    
    if post_id:
        post_path = post_id.replace(":", "/")
        post_url = f"https://{rewst_engine_host}/webhooks/custom/action/{post_path}"
    command_output = await execute_commands(commands, rewst_engine_host, interpreter_override, interpreter_delimiter)
    try:
        message_data = json.loads(command_output)
    except json.JSONDecodeError as e:
        print(f"Error decoding command output as JSON: {e}")
        message_data = {"error": f"Error decoding command output as JSON: {e}", "output": command_output}
    message_json = json.dumps(message_data)
    await device_client.send_message(message_json)
    print("Message sent!")

async def main(check_mode=False):
    global rewst_engine_host
    config_data = load_config()
    if config_data is None:
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
        e = None
        try:
            await device_client.send_message(json.dumps({"test_message": "Test message from device"}))
            print("Check mode: Communication test successful. Test message sent.")
        except Exception as ex:
            e = ex
            print(f"Check mode: Communication test failed. Could not send test message: {e}")
        finally:
            await device_client.disconnect()
            exit(0 if not e else 1)
    else:
        device_client.on_message_received = message_handler
        async def status_update_task():
            while True:
                await send_status_update()
                await asyncio.sleep(status_update_checkin_time)
        status_update_task = asyncio.create_task(status_update_task())
        stop_event = asyncio.Event()
        await stop_event.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--check', action='store_true', help='Run in check mode to test communication')
    args = parser.parse_args()
    asyncio.run(main(check_mode=args.check))
