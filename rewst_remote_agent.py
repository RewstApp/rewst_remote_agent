import argparse
import asyncio
import logging
import platform
import re
import signal
import sys
from config_module.config_io import load_configuration
from iot_hub_module.authentication import authenticate_device, disconnect_device
from iot_hub_module.connection_management import ConnectionManager
from iot_hub_module.error_handling import setup_logging
from iot_hub_module.message_handling import (
    handle_message
)


# Configure logging
setup_logging("RewstRemoteAgent")

os_type = platform.system().lower()

stop_event = asyncio.Event()

if os_type == 'Windows':
    import pywin32
    import win32serviceutil
    from pywin32 import win32api,win32con
    from rewst_service_manager import RewstService


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
        win32api.RegSetValueEx(reg_key, "TypesSupported", 0, win32con.REG_DWORD, win32con.EVENTLOG_ERROR_TYPE | win32con.EVENTLOG_WARNING_TYPE | win32con.EVENTLOG_INFORMATION_TYPE)
    except Exception as e:
        logging.error(f"Failed to set registry values: {e}")
    finally:
        win32api.RegCloseKey(reg_key)


def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}. Initiating graceful shutdown.")
    stop_event.set()


# Main function
async def main(config_file=None):
    logging.info(f"Running on {os_type}")

    app_name = "RewstRemoteAgent"
    if os_type == "Windows":
        await create_event_source(app_name)


    # If Windows, log to event logs
    if os_type == 'Windows':
        nt_event_log_handler = logging.handlers.NTEventLogHandler('RewstService')
        logging.getLogger().addHandler(nt_event_log_handler)

    try:
        logging.info("Loading Configuration")
        if config_file:
            logging.info(f"Using config file {config_file}.")
            config_data = load_configuration(config_file=config_file)
        
        else:
            # Get Org ID for Config
            executable_path = sys.argv[0]  # Gets the file name of the current script
            pattern = re.compile(r'rewst_remote_agent_(.+?)\.')
            match = pattern.search(executable_path)
            if match:
                logging.info("Found GUID")
                org_id = match.group(1)
                logging.info(f"Found Org ID {org_id}")
                config_data = config_io.load_configuration(org_id, None)
            else:
                logging.warning(f"Did not find guid in file {executable_path}")
                config_data = None

        # Exit if no configuration was found
        if not config_data:
            logging.error("No configuration was found. Exiting.")
            exit(1)
        
        # Retrieve org_id from the configuration if it wasn't already found
        if not org_id:
            org_id = config_data['rewst_org_id']
        

    except Exception as e:
        logging.exception(f"Exception Caught during self-configuration: {str(e)}")

    try:
        # Authenticate Device
        logging.info("Authenticating device with IoT Hub...")
        device_client = await authenticate_device(config_data)
        if not device_client:
            logging.error("Failed to authenticate device.")
            return

        # Set Message Handler
        logging.info("Setting message handler...")
        device_client.on_message_received = handle_message
    
    except Exception as e:
        logging.exception(f"Exception Caught during IoT Hub Communications: {str(e)}")

    try:
        while not stop_event.is_set():
            await asyncio.sleep(1)
        disconnect_device()
    except Exception as e:
        logging.exception(f"Exception caught: {str(e)}")


# Entry point
if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--config-file', help='Path to the configuration file.')
    args = parser.parse_args()
    asyncio.run(main(
        config_file=args.config_file
    ))
else:
    if os_type == 'Windows':
        win32serviceutil.HandleCommandLine(RewstService)