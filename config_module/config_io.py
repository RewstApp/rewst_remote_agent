import json
import logging
import os
import platform
from appdirs import (
    AppDirs,
    site_data_dir
)

# Put Timestamps on logging entries
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def get_executable_folder(org_id):
    os_type = platform.system().lower()
    if os_type == "windows":
        program_files_dir = os.environ.get('ProgramFiles')  # This will get the path to Program Files directory
        executable_path = os.path.join(program_files_dir, f"RewstRemoteAgent\\{org_id}\\")
    elif os_type == "linux":
        executable_path = f"/usr/local/bin/"
    elif os_type == "darwin":
        executable_path = os.path.expanduser(f"~/Library/Application Support/RewstRemoteAgent/{org_id}/")
    else:
        logging.error(f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!")
        exit(1)
    return executable_path


def get_service_manager_path(org_id):
    os_type = platform.system().lower()
    if os_type == "windows":
        executable_name = f"rewst_service_manager.win.exe"
    elif os_type == "linux":
        executable_name = f"rewst_service_manager.linux.bin"
    elif os_type == "darwin":
        executable_name = f"rewst_service_manager.macos.bin"
    else:
        logging.error(f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!")
        exit(1)
    executable_path = f"{get_executable_folder(org_id)}{executable_name}"
    return executable_path


def get_agent_executable_path(org_id):
    os_type = platform.system().lower()
    if os_type == "windows":
        executable_name = f"rewst_remote_agent_{org_id}.win.exe"
    elif os_type == "linux":
        executable_name = f"rewst_remote_agent_{org_id}.linux.bin"
    elif os_type == "darwin":
        executable_name = f"rewst_remote_agent_{org_id}.macos.bin"
    else:
        logging.error(f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!")
        exit(1)
    executable_path = f"{get_executable_folder(org_id)}{executable_name}"
    return executable_path


def get_config_file_path(org_id):
    os_type = platform.system().lower()
    logging.info(f"Returning {os_type} config file path.")
    if os_type == "windows":
        config_dir = AppDirs(org_id, 'RewstRemoteAgent').site_config_dir
    elif os_type == "linux":
        config_dir = f"/etc/rewst_remote_agent/{org_id}/"
    elif os_type == "darwin":
        config_dir = os.path.expanduser(f"~/Library/Application Support/RewstRemoteAgent/{org_id}/")
    else:
        logging.error(f"Unsupported OS type: {os_type}. Send this output to Rewst for investigation!")
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


def save_configuration(config_data, config_file=None):
    org_id = config_data["rewst_org_id"]
    config_file_path = get_config_file_path(org_id)
    with open(config_file_path, 'w') as f:
        json.dump(config_data, f, indent=4)
        logging.info(f"Configuration saved to {config_file_path}")


def load_configuration(org_id=None, config_file=None):
    config_file_path = get_config_file_path(org_id)
    try:
        with open(config_file_path) as f:
            logging.info(f"Configuration loading from {config_file_path}")
            return json.load(f)
    except FileNotFoundError:
        logging.exception("Error: Configuration File not found")
        return None
