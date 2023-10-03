import asyncio
import json
from azure.iot.device.aio import IoTHubDeviceClient

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
    
    # Send a single message
    print("Sending message...")
    await device_client.send_message("Hello, IoT Hub!")
    print("Message sent!")
    
    # Disconnect from the IoT hub
    print("Disconnecting from IoT Hub...")
    await device_client.disconnect()
    print("Disconnected!")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
