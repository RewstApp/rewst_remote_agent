import asyncio
import json
import subprocess
import os
import tempfile
import argparse
import psutil
from concurrent.futures import ThreadPoolExecutor
from azure.iot.device.aio import IoTHubDeviceClient

executor = ThreadPoolExecutor()

async def send_status_update():
    # Collect status data
    status_data = {
        "cpu_usage": psutil.cpu_percent(interval=1),  # CPU usage percentage
        "memory_usage": psutil.virtual_memory().percent,  # Memory usage percentage
        "disk_usage": psutil.disk_usage('/').percent,  # Disk usage percentage for the root directory
        "network_io": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv
        }  # Network IO statistics
    }
    
    # Create message object
    message_json = json.dumps(status_data)
    
    # Send message
    print("Sending status update to IoT Hub...")
    await device_client.send_message(message_json)
    print("Status update sent!")


def get_connection_string():
    try:
        with open('config.json') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    required_keys = ['azure_iot_hub_host', 'device_id', 'shared_access_key']
    for key in required_keys:
        if key not in config:
            print(f"Error: Missing '{key}' in configuration.")
            return None
    
    conn_str = f"HostName={config['azure_iot_hub_host']};DeviceId={config['device_id']};SharedAccessKey={config['shared_access_key']}"
    return conn_str

def message_handler(message):
    print(f"Received message: {message.data}")
    message_data = json.loads(message.data)
    if "commands" in message_data:
        commands = message_data["commands"]
        print("Running commands")
        executor.submit(run_handle_commands, commands)

def run_handle_commands(commands):
    asyncio.run(handle_commands(commands))

async def execute_commands(commands):
    command_results = []
    with subprocess.Popen("/bin/bash", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
        for command in commands:
            process.stdin.write(command + '\n')
            process.stdin.flush()
            output, error = process.communicate()
            command_results.append(output.strip() if output else "")
    return command_results

async def handle_commands(commands):
    command_results = await execute_commands(commands)
    message_data = {"command_results": command_results}
    message_json = json.dumps(message_data)
    print("Sending message to IoT Hub...")
    await device_client.send_message(message_json)
    print("Message sent!")

async def main(check_mode=False):
    conn_str = get_connection_string()
    if conn_str is None:
        return

    global device_client
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    
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
        device_client.on_message_received_handler = message_handler
    
        async def status_update_task():
            while True:
                await send_status_update()
                await asyncio.sleep(60)  # Send status update every 60 seconds
        status_update_task = asyncio.create_task(status_update_task())
                  
        stop_event = asyncio.Event()
        await stop_event.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--check', action='store_true', help='Run in check mode to test communication')
    args = parser.parse_args()
    
    asyncio.run(main(check_mode=args.check))
