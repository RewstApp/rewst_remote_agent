import logging
from azure.iot.device.aio import IoTHubDeviceClient

def get_connection_string(config):
    """
    Constructs a connection string from the provided configuration.

    :param config: The configuration dictionary.
    :return: The connection string.
    """
    conn_str = (
        f"HostName={config['azure_iot_hub_host']};"
        f"DeviceId={config['device_id']};"
        f"SharedAccessKey={config['shared_access_key']}"
    )
    return conn_str

async def authenticate_device(config):
    """
    Authenticates the device with Azure IoT Hub.

    :param config: The configuration dictionary.
    :return: The authenticated device client.
    """
    connection_string = get_connection_string(config)
    device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)

    logging.info("Connecting to IoT Hub...")
    await device_client.connect()
    logging.info("Connected!")

    return device_client

async def disconnect_device(device_client):
    """
    Disconnects the device from Azure IoT Hub.

    :param device_client: The authenticated device client.
    """
    logging.info("Disconnecting from IoT Hub...")
    await device_client.disconnect()
    logging.info("Disconnected!")
