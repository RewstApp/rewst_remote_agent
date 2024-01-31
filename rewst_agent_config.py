import argparse
import asyncio
import logging
import os
import platform
import re
import subprocess
import sys
from urllib.parse import urlparse
from config_module.config_io import (
    get_service_manager_path,
    get_agent_executable_path,
    get_service_executable_path,
    save_configuration
)
from config_module.fetch_config import fetch_configuration
from iot_hub_module.connection_management import ConnectionManager
from service_module.service_management import is_service_running

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logging.info(f"Running on {platform.system()} {platform.release()}")

os_type = platform.system().lower()


def is_valid_url(url):
    # Check if the URL is parsable
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        logging.error(f"The provided string {url} is not a valid URL")
        return False


def is_base64(sb):
    # Check if it's a base64 string by regex for valid characters
    try:
        if isinstance(sb, str):
            # If there's any whitespace, remove it
            sb = sb.strip()
        if bool(re.match('^[A-Za-z0-9+/]+={0,2}$', sb)):
            return True
        return False
    except Exception as e:
        print(e)
        return False


async def remove_old_files(org_id):
    # Determine the file paths using functions from config_io.py
    service_manager_path = get_service_manager_path(org_id)
    agent_executable_path = get_agent_executable_path(org_id)
    file_paths = [service_manager_path, agent_executable_path]

    if os_type == "windows":
        service_executable_path = get_service_executable_path(org_id)
        file_paths.append(service_executable_path)

    for file_path in file_paths:
        if os.path.exists(file_path):
            # Construct the new file name with '_oldver'
            new_file_path = f"{file_path}_oldver"
            try:
                # cycle out old versions
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                os.rename(file_path, new_file_path)
                logging.info(f"Renamed {file_path} to {new_file_path}")
            except OSError as e:
                logging.error(f"Error renaming file {file_path}: {e}")


async def wait_for_files(org_id, timeout=3600) -> bool:
    logging.info("Waiting for files to be written...")
    # Determine the file paths using functions from config_io.py
    service_manager_path = get_service_manager_path(org_id)
    logging.info(f"Awaiting Service Manager File: {service_manager_path} ...")

    agent_executable_path = get_agent_executable_path(org_id)
    logging.info(f"Awaiting Agent Service File: {agent_executable_path} ...")

    file_paths = [service_manager_path, agent_executable_path]

    if os_type == "windows":
        service_executable_path = get_service_executable_path(org_id)
        logging.info(f"Awaiting Service Executable File: {service_executable_path} ...")
        file_paths.append(service_executable_path)

    start_time = asyncio.get_running_loop().time()

    while True:
        # Check if all files exist
        all_files_exist = all(os.path.exists(file_path) for file_path in file_paths)
        if all_files_exist:
            await asyncio.sleep(20)
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

    # Obtain the explicit path to the rewst_service_manager executable
    service_manager_path = get_service_manager_path(org_id)

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


def end_program(exit_level=1):
    logging.info(f"Agent configuration is exiting with exit level {exit_level}.")
    sys.exit(exit_level)


async def main(config_url, config_secret, org_id):

    # Check URL and Secret for valid strings
    if not is_valid_url(config_url):
        logging.error("The config URL provided is not valid.")
        end_program(1)
    if not is_base64(config_secret):
        logging.error("The config secret provided is not a valid base64 string.")
        end_program(1)

    try:
        # Check that arguments are provided
        if not (config_url and config_secret and org_id):
            print("Error: Missing required parameters.")
            print("Please make sure '--config-url', '--org-id' and '--config-secret' are provided.")
            end_program(1)

        # Fetch Configuration
        logging.info("Fetching configuration from Rewst...")
        url_org_id = config_url.split("/")[-1]
        config_data = await fetch_configuration(config_url, config_secret, org_id)
        if not config_data:
            logging.error("Failed to fetch configuration.")
            end_program(2)

        # Save Configuration to JSON file
        logging.info("Saving configuration to file...")
        save_configuration(config_data)

        # Show Config JSON
        logging.info(f"Configuration: {config_data}")

        org_id = config_data['rewst_org_id']
        logging.info(f"Organization ID: {org_id}")

        # Instantiate ConnectionManager
        connection_manager = ConnectionManager(config_data)

        # Connect to IoT Hub
        logging.info("Connecting to IoT Hub...")
        await connection_manager.connect()

        # Set Message Handler
        logging.info("Setting up message handler...")
        await connection_manager.set_message_handler()

        # Move Existing files to _oldver
        await remove_old_files(org_id)

        # Wait for files to be written
        await wait_for_files(org_id)

        # Disconnect from IoT Hub to not conflict with the Service
        logging.info("Disconnecting from IoT Hub...")
        await connection_manager.disconnect()
        await asyncio.sleep(4)
        logging.info("Disconnected from IoT Hub.")

        while not (is_service_running(org_id)):
            logging.info("Waiting for the service to start...")
            await asyncio.sleep(5)  # Sleep for 5 seconds before checking the status again

        end_program(0)

    except Exception as e:
        logging.exception(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Rewst Agent Configuration Tool.')
    parser.add_argument('--config-secret', help='Secret Key for configuration access')
    parser.add_argument('--config-url', help='URL to fetch the configuration from.')
    parser.add_argument('--org-id', help='Organization ID to register agent within.')
    args = parser.parse_args()  # Extract arguments from the parser
    asyncio.run(main(
        config_secret=args.config_secret,
        config_url=args.config_url,
        org_id=args.org_id,
    ))
