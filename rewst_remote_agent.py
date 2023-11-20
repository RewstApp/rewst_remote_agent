import asyncio
from asyncio import Event
import logging
import platform
import re
import signal
import sys
from __version__ import __version__
from argparse import ArgumentParser
from config_module.config_io import (
    load_configuration
)
from iot_hub_module.connection_management import (
    ConnectionManager
)

os_type = platform.system().lower()

if os_type == "windows":
    import pywin32
    from pywin32 import (
        win32con,
        win32api
    )

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

stop_event = Event()


# Sets up event log handling
async def create_event_source(app_name):
    registry_key = f"SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{app_name}"
    key_flags = win32con.KEY_SET_VALUE | win32con.KEY_CREATE_SUB_KEY
    try:
        # Try to open the registry key
        reg_key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, registry_key, 0, key_flags)
    except Exception as e:
        logging.error(f"Failed to open or create registry key: {e}")
        return

    try:
        # Set the EventMessageFile registry value
        event_message_file = win32api.GetModuleHandle(None)
        win32api.RegSetValueEx(reg_key, "EventMessageFile", 0, win32con.REG_SZ, event_message_file)
        win32api.RegSetValueEx(reg_key, "TypesSupported", 0, win32con.REG_DWORD,
                               win32con.EVENTLOG_ERROR_TYPE | win32con.EVENTLOG_WARNING_TYPE | win32con.EVENTLOG_INFORMATION_TYPE)
    except Exception as e:
        logging.error(f"Failed to set registry values: {e}")
    finally:
        win32api.RegCloseKey(reg_key)


def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}. Initiating graceful shutdown.")
    stop_event.set()


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


# Set the status update interval
status_update_checkin_time = 600


# Main function
async def main(config_file=None):
    logging.info(f"Version: {__version__}")
    logging.info(f"Running on {os_type}")

    org_id = None
    app_name = "RewstRemoteAgent"

    # Set up Event Logs for Windows
    if os_type == "windows":
        await create_event_source(app_name)
        nt_event_log_handler = logging.handlers.NTEventLogHandler('RewstService')
        logging.getLogger().addHandler(nt_event_log_handler)

    try:
        logging.info("Loading Configuration")
        if config_file:
            logging.info(f"Using config file {config_file}.")
            config_data = load_configuration(None, config_file)
            org_id = config_data['rewst_org_id']

        else:
            # Get Org ID for Config
            executable_path = sys.argv[0]  # Gets the file name of the current script
            pattern = re.compile(r'rewst_remote_agent_(.+?)\.')
            match = pattern.search(executable_path)
            if match:
                logging.info("Found GUID")
                org_id = match.group(1)
                logging.info(f"Found Org ID {org_id}")
                config_data = load_configuration(org_id)
            else:
                logging.warning(f"Did not find guid in file {executable_path}")
                config_data = None

        # Exit if no configuration was found
        if not config_data:
            logging.error("No configuration was found. Exiting.")
            exit(1)

    except Exception as e:
        logging.exception(f"Exception Caught during self-configuration: {str(e)}")
        exit(1)

    logging.info(f"Running for Org ID {org_id}")

    try:
        # Instantiate ConnectionManager
        connection_manager = ConnectionManager(config_data)

        # Connect to IoT Hub
        logging.info("Connecting to IoT Hub...")
        await connection_manager.connect()

        # Set Message Handler
        logging.info("Setting up message handler...")
        await connection_manager.set_message_handler()

        while not stop_event.is_set():
            await asyncio.sleep(1)

        await connection_manager.disconnect()

    except Exception as e:
        logging.exception(f"Exception Caught during IoT Hub Loop: {str(e)}")
        exit(1)

    while not stop_event.is_set():
        await asyncio.sleep(1)

# Entry point
if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    parser = ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--config-file', help='Path to the configuration file.')
    args = parser.parse_args()
    asyncio.run(main(
        config_file=args.config_file
    ))

