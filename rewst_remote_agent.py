import asyncio
import logging
import logging.handlers
import platform
import signal
import sys
from __version__ import __version__
from argparse import ArgumentParser
from config_module.config_io import (
    load_configuration,
    get_org_id_from_executable_name
)

os_type = platform.system().lower()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


# Main function
async def main():

    logging.info(f"Version: {__version__}")
    logging.info(f"Running on {os_type}")

    parser = ArgumentParser(description='Rewst Service Manager.')

    # Check if running as a Windows service
    running_as_win_service = False
    if os_type == "windows" and len(sys.argv) > 1:
        if sys.argv[1] in ['start', 'stop', 'restart']:
            logging.info(f"Running as Windows Service with argument: {sys.argv[1]}")
            running_as_win_service = True

    if not running_as_win_service:
        parser.add_argument('--foreground', action='store_true', help='Run the service in foreground mode.')
        args = parser.parse_args()
        foreground = args.foreground
    else:
        foreground = False

    config_file = None
    stop_event = asyncio.Event()

    if foreground:
       logging.info("Running in foreground mode")

    def signal_handler():
        logging.info("Shutting down gracefully.")
        stop_event.set()

    try:
        logging.info("Loading Configuration")
        if config_file:
            logging.info(f"Using config file {config_file}.")
            config_data = load_configuration(None, config_file)
            org_id = config_data['rewst_org_id']

        else:
            org_id = get_org_id_from_executable_name(sys.argv)
            if org_id:
                logging.info(f"Found Org ID {org_id}")
                config_data = load_configuration(org_id)
            else:
                logging.warning(f"Did not find guid in executable name")
                config_data = None

        # Exit if no configuration was found
        if not config_data:
            raise ConfigurationError("No configuration was found.")

    except ConfigurationError as e:
        logging.error(str(e))
        return
    except Exception as e:
        logging.exception(f"Exception Caught during self-configuration: {str(e)}")
        return

    logging.info(f"Running for Org ID {org_id}")

    if os_type == "windows":
        if foreground:
            logging.info("Beginning foreground loop")
            from iot_hub_module.connection_management import (
                iot_hub_connection_loop
            )
            await iot_hub_connection_loop(config_data, stop_event)
        else:
            logging.info("Running Service Logic")
            import win32serviceutil
            from service_module.windows_service import (
                RewstWindowsService
            )
            RewstWindowsService.config_data = config_data
            RewstWindowsService.set_service_name(org_id)
            win32serviceutil.HandleCommandLine(RewstWindowsService)
    else:
        from iot_hub_module.connection_management import (
            iot_hub_connection_loop
        )
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
        from iot_hub_module.connection_management import iot_hub_connection_loop
        await iot_hub_connection_loop(config_data, stop_event)


# Entry point
if __name__ == "__main__":
    # parser = ArgumentParser(description='Run the IoT Hub device client.')
    # parser.add_argument('--config-file', help='Path to the configuration file.')
    # parser.add_argument('start', required=False, help='Start the service.')
    # parser.add_argument('restart', required=False, help='Restart the service.')
    # parser.add_argument('stop', reuqire=False, help='Stop the service.')
    # parser.add_argument('--foreground', required=False, help='Run the service in foreground mode.', type=bool)
    # args = parser.parse_args()

    asyncio.run(main())
