import asyncio
import logging
import logging.handlers
import platform
import sys
from __version__ import __version__
from argparse import ArgumentParser
from config_module.config_io import (
    load_configuration,
    get_org_id_from_executable_name
)

os_type = platform.system().lower()

if os_type == "windows":
    import win32serviceutil
    from service_module.windows_service import (
        RewstWindowsService
    )
else:
    from iot_hub_module.connection_management import (
        iot_hub_connection_loop
    )

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


# Main function
async def main(config_file=None):
    logging.info(f"Version: {__version__}")
    logging.info(f"Running on {os_type}")

    org_id = None

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
            logging.error("No configuration was found. Exiting.")
            exit(1)

    except Exception as e:
        logging.exception(f"Exception Caught during self-configuration: {str(e)}")
        exit(1)

    logging.info(f"Running for Org ID {org_id}")

    if os_type == "windows":
        service = RewstWindowsService(None)
        service.set_up(org_id)

    else:
        await iot_hub_connection_loop(config_data)

# Entry point
if __name__ == "__main__":
    parser = ArgumentParser(description='Run the IoT Hub device client.')
    parser.add_argument('--config-file', help='Path to the configuration file.')
    args = parser.parse_args()

    if os_type == "windows":
        win32serviceutil.HandleCommandLine(RewstWindowsService)
    else:
        asyncio.run(main(
            config_file=args.config_file
        ))
