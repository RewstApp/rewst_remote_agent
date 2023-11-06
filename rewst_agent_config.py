import argparse
import asyncio
import base64
import logging
import os
import subprocess
import sys
from urllib.parse import urlparse
from config_module.config_io import (
    get_service_manager_path,
    get_agent_executable_path,
    save_configuration,
    load_configuration
)
from config_module.fetch_config import fetch_configuration
from iot_hub_module import authentication, connection_management, message_handling


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def is_valid_url(url):
    # Check if the URL is parsable
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
        logging.info("URL is valid.")
    except ValueError:
        return False


def is_base64(s):
     # Check if it's a base64 string by trying to decode it
    try:
        base64.b64decode(s)
        return True
    except base64.binascii.Error:
        return False

async def wait_for_files(org_id, timeout=3600) -> bool:
    """
    Waits for the service manager and service agent executables to be written to the filesystem.

    :param org_id: The organization ID used to construct the file paths.
    :param timeout: The maximum time to wait, in seconds. Default is 3600 seconds (60 minutes).
    :return: True if both files were written, False if the timeout was reached.
    """
    # Determine the file paths using functions from config_io.py
    service_manager_path = get_service_manager_path(org_id)
    agent_executable_path = get_agent_executable_path(org_id)
    file_paths = [service_manager_path, agent_executable_path]

    start_time = asyncio.get_running_loop().time()
    while True:
        # Check if all files exist
        all_files_exist = all(os.path.exists(file_path) for file_path in file_paths)
        if all_files_exist:
            logging.info("All files have been written.")
            return True

        # Check if the timeout has been reached
        elapsed_time = asyncio.get_running_loop().time() - start_time
        if elapsed_time > timeout:
            logging.warning("Timeout reached while waiting for files.")
            return False

        # Wait before checking again
        await asyncio.sleep(5)  # sleep for 5 seconds before checking again


async def install_and_start_service(org_id):
    """
    Installs and starts the service using the rewst_service_manager executable.
    
    :param org_id: The organization ID used to determine the executable path.
    :return: True if the service was successfully installed and started, False otherwise.
    """
    # Obtain the explicit path to the rewst_service_manager executable
    service_manager_path = get_service_manager_path(org_id)

    # Command to install the service
    install_command = [service_manager_path, '--org-id', org_id, '--install']
    try:
        process = await asyncio.create_subprocess_exec(
            *install_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logging.info("Service installed successfully.")
        else:
            logging.error(f"Failed to install the service: {stderr.decode().strip()}")
            return False
    except Exception as e:
        logging.error(f"Failed to install the service: {e}")
        return False
    
    # Command to start the service
    start_command = [service_manager_path, '--org-id', org_id, '--start']
    try:
        subprocess.run(start_command, check=True, text=True)
        logging.info("Service started successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to start the service: {e}")
        return False
    
    return True


async def check_service_status(org_id):
    """
    Checks the status of the service using the rewst_service_manager executable.
    
    :param org_id: The organization ID used to determine the executable path.
    :return: True if the service is running, False otherwise.
    """
    # Obtain the explicit path to the rewst_service_manager executable
    service_manager_path = config_io.get_service_manager_path(org_id)

    # Command to check the service status
    status_command = [service_manager_path, '--org-id', org_id, '--status']
    try:
        result = subprocess.run(status_command, check=True, text=True, capture_output=True)
        output = result.stdout.strip()
        logging.info(f"Service status: {output}")
        return "running" in output.lower()
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to check the service status: {e}")
        return False


def end_program(exit_level=1,service_status=None):
    logging.info(f"Agent configuration is exiting with exit level {exit_level}.")
    exit(exit_level)


async def main(config_url, config_secret):
    
    # Check URL and Secret for valid strings
    if not is_valid_url(config_url):
        logging.error("The config URL provided is not valid.")
        end_program(1)
    if not is_base64(config_secret):
        logging.error("The config secret provided is not a valid base64 string.")
        end_program(1)

    try:
        # Check that arguments are provided
        if not config_url or not config_secret:
            print("Error: Missing required parameters.")
            print("Please make sure '--config-url' and '--config-secret' are provided.")
            sys.exit(1)  # Exit with a non-zero status to indicate an error
        
        # Fetch Configuration
        logging.info("Fetching configuration from Rewst...")
        config_data = await fetch_configuration(config_url, config_secret)
        if not config_data:
            logging.error("Failed to fetch configuration.")
            return

        # Save Configuration to JSON file
        logging.info("Saving configuration to file...")
        save_configuration(config_data)

        # Load Configurationg
        logging.info("Loading configuration from file...")
        config = load_configuration()

        org_id = config["rewst_org_id"]

        # Authenticate Device
        logging.info("Authenticating device with IoT Hub...")
        device_client = await authentication.authenticate_device(config)
        if not device_client:
            logging.error("Failed to authenticate device.")
            return

        # Set Message Handler
        logging.info("Setting message handler...")
        device_client.on_message_received = message_handling.handle_message

        # Await 'command' message and execute commands
        # This part will be handled by the message handler set above

        # Wait for files to be written
        await wait_for_files(org_id)
        
        # Disconnect from IoT Hub to not conflict with the Service
        logging.info("Disconnecting from IoT Hub...")
        await device_client.disconnect()
        await asyncio.sleep(4)
        logging.info("Disconnected from IoT Hub.")

        if (await install_and_start_service(org_id)):
        # Wait for the service to start successfully
            while not (await check_service_status(org_id)):
                logging.info("Waiting for the service to start...")
                await asyncio.sleep(5)  # Sleep for 5 seconds before checking the status again

            logging.info("Service started successfully.")
            logging.info("Exiting the program with success.")
            exit_level = 0
        else:
            logging.error("Failed to install or start the service.")
            logging.error("Exiting the program with failure.")
            exit_level = 1
        
        end_program(exit_level)

    except Exception as e:
        logging.exception(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Rewst Agent Configuration Tool.')
    parser.add_argument('--config-secret', help='Path to the configuration file.')
    parser.add_argument('--config-url', help='URL to fetch the configuration from.')
    args = parser.parse_args()  # Extract arguments from the parser
    asyncio.run(main(
            config_secret=args.config_secret,
            config_url=args.config_url
    ))