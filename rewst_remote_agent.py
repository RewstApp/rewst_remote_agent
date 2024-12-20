""" Module for executing the remote agent """

import asyncio
import logging
import logging.handlers
import platform
import signal
import sys
from __version__ import __version__
from config_module.config_io import (
    load_configuration,
    get_org_id_from_executable_name,
    setup_file_logging,
)
from iot_hub_module.connection_management import iot_hub_connection_loop

os_type = platform.system().lower()

stop_event = asyncio.Event()


class ConfigurationError(Exception):
    """ Configuration error class """
    pass


def signal_handler() -> None:
    """
    Signal handler used in the application.
    """    
    logging.info("Shutting down gracefully.")
    stop_event.set()


# Main function
async def main() -> None:
    """
    Main entry point of the program

    Raises:
        ConfigurationError: if the configuration failed.
    """

    logging.info(f"Version: {__version__}")
    logging.info(f"Running on {os_type}")

    config_file = None

    try:
        logging.info("Loading Configuration")
        if config_file:
            logging.info(f"Using config file {config_file}.")
            config_data = load_configuration(None, config_file)
            org_id = config_data["rewst_org_id"]

        else:
            org_id = get_org_id_from_executable_name(sys.argv)
            if org_id:
                logging.info(f"Found Org ID {org_id} via executable name.")
                config_data = load_configuration(org_id)
            else:
                logging.warning(f"Did not find guid in executable name.")
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

    logging.info("Setting up file logging")
    try:
        setup_file_logging(org_id)
    except Exception as e:
        logging.exception(f"Exception occurred setting up file-based logging: {e}.")

    if os_type != "windows":
        # Register signal handlers for Unix-based systems
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

    await iot_hub_connection_loop(config_data, stop_event)


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
