import asyncio
import json
from azure.iot.device.aio import IoTHubDeviceClient

async def execute_commands(commands):
    command_results = []
    with subprocess.Popen("/bin/bash", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
        for command in commands:
            process.stdin.write(command + '\n')
            process.stdin.flush()
            output, error = process.communicate()
            command_results.append(output.strip() if output else "")
    return command_results

def message_handler(message):
    message_data = json.loads(message.data)
    print
    if "commands" in message_data:
        commands = message_data["commands"]
        print("running commands")
        asyncio.create_task(handle_commands(commands))

async def handle_commands(commands):
    command_results = await execute_commands(commands)
    # Collect command results to send back to IoT Hub
    print(command_results)  # Just printing the results for now

def message_handler(message):
    print(f"Received message: {message.data}")

async def main():
    try:
        # Attempt to load configuration from JSON file
        with open('config.json') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: Configuration file 'config.json' not found.")
        return
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from 'config.json'.")
        return
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading 'config.json': {e}")
        return
    
    # Ensure all necessary configuration keys are present
    required_keys = ['azure_iot_hub_host', 'device_id', 'shared_access_key']
    for key in required_keys:
        if key not in config:
            print(f"Error: Missing '{key}' in configuration.")
            return

    # Build the connection string
    conn_str = f"HostName={config['azure_iot_hub_host']};DeviceId={config['device_id']};SharedAccessKey={config['shared_access_key']}"
    
    # Create instance of the device client using the connection string
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    
    # Connect to the IoT hub
    print("Connecting to IoT Hub...")
    await device_client.connect()
    
    # Set the message handler
    device_client.on_message_received = message_handler
    
    # Create an event that will never be set to keep the script running
    stop_event = asyncio.Event()
    await stop_event.wait()

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())