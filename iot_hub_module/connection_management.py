from azure.iot.device.aio import IoTHubDeviceClient


class ConnectionManager:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.client = IoTHubDeviceClient.create_from_connection_string(self.connection_string)

    async def connect(self):
        await self.client.connect()

    async def disconnect(self):
        await self.client.disconnect()

    async def send_message(self, message):
        await self.client.send_message(message)

    async def set_message_handler(self, message_handler):
        self.client.on_message_received = message_handler

# Usage example:
# connection_manager = ConnectionManager(connection_string)
# await connection_manager.connect()
# await connection_manager.send_message("Hello, IoT Hub!")
# await connection_manager.set_message_handler(my_message_handler)  # where my_message_handler is a coroutine
# await connection_manager.disconnect()
