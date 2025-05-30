""" Module providing functions to manage configuration """

from typing import Dict, Any, List

import json
import logging
import os
import platform
import re
from logging.handlers import RotatingFileHandler
from platformdirs import site_config_dir

# Put Timestamps on logging entries
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

os_type = platform.system().lower()


def get_executable_folder(org_id: str) -> str:
    """
    Get executable folder path of the organization.

    Args:
        org_id (str): Organization identifier in Rewst platform.

    Returns:
        str: Executable folder path.
    """
    os_type = platform.system().lower()
    if os_type == "windows":
        # This will get the path to Program Files directory
        program_files_dir = os.environ.get("ProgramFiles")
        executable_path = os.path.join(
            program_files_dir, f"RewstRemoteAgent\\{org_id}\\"
        )
    elif os_type == "linux":
        executable_path = f"/usr/local/bin/"
    elif os_type == "darwin":
        executable_path = os.path.expanduser(
            f"~/Library/Application Support/RewstRemoteAgent/{org_id}/"
        )
    else:
        logging.error(
            f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!"
        )
        exit(1)
    return executable_path


def get_service_manager_path(org_id: str) -> str:
    """
    Get service manager file path of the organization.

    Args:
        org_id (str): Organization identifier in Rewst platform.

    Returns:
        str: Service manager file path.
    """
    if os_type == "windows":
        executable_name = f"rewst_service_manager.win_{org_id}.exe"
    elif os_type == "linux":
        executable_name = f"rewst_service_manager.linux_{org_id}.bin"
    elif os_type == "darwin":
        executable_name = f"rewst_service_manager.macos_{org_id}.bin"
    else:
        logging.error(
            f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!"
        )
        exit(1)
    executable_path = f"{get_executable_folder(org_id)}{executable_name}"
    return executable_path


def get_agent_executable_path(org_id: str) -> str:
    """
    Get agent executable file path.

    Args:
        org_id (str): Organization identifier in Rewst platform.

    Returns:
        str: Agent executable file path.
    """
    if os_type == "windows":
        executable_name = f"rewst_remote_agent_{org_id}.win.exe"
    elif os_type == "linux":
        executable_name = f"rewst_remote_agent_{org_id}.linux.bin"
    elif os_type == "darwin":
        executable_name = f"rewst_remote_agent_{org_id}.macos.bin"
    else:
        logging.error(
            f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!"
        )
        exit(1)
    executable_path = f"{get_executable_folder(org_id)}{executable_name}"
    return executable_path


def get_service_executable_path(org_id: str) -> str:
    """
    Get service executable file path.

    Args:
        org_id (str): Organization identifier in Rewst platform.

    Returns:
        str: Service executable file path.
    """
    if os_type == "windows":
        executable_name = f"rewst_windows_service_{org_id}.win.exe"
        executable_path = f"{get_executable_folder(org_id)}{executable_name}"
    else:
        logging.info(
            f"Windows Service executable is only necessary for Windows, not {os_type}"
        )
        executable_path = None
    return executable_path


def get_logging_path(org_id: str) -> str:
    """
    Get logging file path.

    Args:
        org_id (str): Organization identifier in Rewst platform.

    Returns:
        str: Logging file path.
    """
    base_dir = site_config_dir()
    log_filename = "rewst_agent.log"
    if os_type == "windows":
        log_path = f"{base_dir}\\RewstRemoteAgent\\{org_id}\\logs\\{log_filename}"
    elif os_type == "linux":
        log_path = f"/var/log/rewst_remote_agent/{org_id}/{log_filename}"
    elif os_type == "darwin":
        log_path = f"/var/log/rewst_remote_agent/{org_id}/{log_filename}"
    else:
        logging.error(
            f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!"
        )
        exit(1)
    logging.info(f"Logging to: {log_path}")
    return log_path


def get_config_file_path(org_id: str) -> str:
    """
    Get config file path.

    Args:
        org_id (str): Organization identifier in Rewst platform.

    Returns:
        str: Config file path.
    """
    base_dir = site_config_dir()
    logging.info(f"Returning {os_type} config file path.")
    if os_type == "windows":
        config_dir = f"{base_dir}\\RewstRemoteAgent\\{org_id}"
    elif os_type == "linux":
        config_dir = f"/etc/rewst_remote_agent/{org_id}/"
    elif os_type == "darwin":
        config_dir = os.path.expanduser(
            f"~/Library/Application Support/RewstRemoteAgent/{org_id}/"
        )
    else:
        logging.error(
            f"Unsupported OS type: {
                      os_type}. Send this output to Rewst for investigation!"
        )
        exit(1)
    logging.info(f"path: {config_dir}")

    if not os.path.exists(config_dir):
        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
        except Exception as e:
            logging.error(f"Failed to create directory {config_dir}: {str(e)}")
            raise

    config_file_path = os.path.join(config_dir, "config.json")
    logging.info(f"Config File Path: {config_file_path}")
    return config_file_path


def save_configuration(config_data: Dict[str, Any], config_file: str = None) -> None:
    """
    Save configuration of the config_data to the file path.

    Args:
        config_data (Dict[str, Any]): Configuration data object.
        config_file (str, optional): Configuration file path. Defaults to None.
    """
    org_id = config_data["rewst_org_id"]
    config_file_path = get_config_file_path(org_id)
    with open(config_file_path, "w") as f:
        json.dump(config_data, f, indent=4)
        logging.info(f"Configuration saved to {config_file_path}")


def load_configuration(
    org_id: str = None, config_file_path: str = None
) -> Dict[str, Any] | None:
    """
    Load configuration for the organization from configuration file path.

    Args:
        org_id (str, optional): Organization identifier in Rewst platform. Defaults to None.
        config_file_path (str, optional): Config file path. Defaults to None.

    Returns:
        Dict[str, Any]|None: Load configuration JSON object if file exists, otherwise None.
    """
    if not config_file_path:
        config_file_path = get_config_file_path(org_id)
    try:
        with open(config_file_path) as f:
            logging.info(f"Configuration loading from {config_file_path}")
            return json.load(f)
    except FileNotFoundError:
        logging.exception("Error: Configuration File not found")
        return None


def get_org_id_from_executable_name(commandline_args: List[str]) -> str | bool:
    """
    Get organization identifier from the executable filename.

    Args:
        commandline_args (List[str]): Command line arguments used to run the executable.

    Returns:
        str|bool: Organization identifier if present, otherwise False.
    """
    # Gets the file name of the current script
    executable_path = commandline_args[0]
    # pattern = re.compile(r'rewst_remote_agent_(.+?)\.')
    pattern = re.compile(r"rewst_.*_(.+?)\.")
    match = pattern.search(executable_path)
    if match:
        return match.group(1)
    return False


def setup_file_logging(org_id: str = None) -> bool:
    """
    Setup the logging system for the organization.

    Args:
        org_id (str, optional): Organization identifier in the Rewst platform. Defaults to None.

    Returns:
        bool: True if setup is successful, otherwise False.
    """
    log_file_path = get_logging_path(org_id)
    print(f"Configuring logging to file: {log_file_path}")  # Debug print
    try:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        file_handler = RotatingFileHandler(log_file_path, maxBytes=10485760, backupCount=3)
        file_handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        file_handler.setLevel(logging.INFO)

        logging.getLogger().addHandler(file_handler)
        logging.info("File Logging initialized.")
        
        return True
    except Exception as e:
        print(f"Exception setting up file logging: {e}")  # Debug print
        return False
