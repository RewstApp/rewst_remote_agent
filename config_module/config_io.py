import json
import logging
import os
import platform


# Put Timestamps on logging entries
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def get_executable_folder(org_id):
    os_type = platform.system().lower()
    if os_type == "Windows":
        program_files_dir = os.environ.get('ProgramFiles')  # This will get the path to Program Files directory
        executable_path = os.path.join(program_files_dir, f"RewstRemoteAgent\\{org_id}")
    elif os_type == "Linux":
        executable_path = f"/usr/local/bin"
    elif os_type == "Darwin":
        executable_path = os.path.expanduser(f"~/Library/Application Support/RewstRemoteAgent")
    return executable_path

def get_service_manager_path(org_id):
    os_type = platform.system().lower()
    if os_type == "Windows":
        executable_name = f"rewst_service_manager.win.exe"
    elif os_type == "Linux":
        executable_name = f"rewst_service_manager.linux.bin"
    elif os_type == "Darwin":
        executable_name = f"rewst_service_manager.macos.bin"
    executable_path = f"{get_executable_folder()}{executable_name}"
    return executable_path

def get_agent_executable_path(org_id):
    os_type = platform.system().lower()
    if os_type == "Windows":
        executable_name = f"rewst_remote_agent_{org_id}.win.exe"
    elif os_type == "Linux":
        executable_name = f"rewst_remote_agent_{org_id}.linux.bin"
    elif os_type == "Darwin":
        executable_name = f"rewst_remote_agent_{org_id}.macos.bin"
    executable_path = f"{get_executable_folder()}{executable_name}"
    return executable_path

def get_config_file_path(org_id=None, config_file=None):
    if config_file:
        return config_file
    os_type = platform.system()
    if os_type == "Windows":
        config_dir = os.path.join(os.environ.get('PROGRAMDATA'), 'RewstRemoteAgent', org_id if org_id else '',"\\")
    elif os_type == "Linux":
        config_dir = f"/etc/rewst_remote_agent/{org_id}/"
    elif os_type == "Darwin":
        config_dir = os.path.expanduser(f"~/Library/Application Support/RewstRemoteAgent/{org_id}/")
    
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
    config_file_path = get_config_file_path(org_id, config_file)
    with open(config_file_path, 'w') as f:
        json.dump(config_data, f, indent=4)
        logging.info(f"Configuration saved to {config_file_path}")

def load_configuration(org_id=None, config_file=None):
    config_file_path = get_config_file_path(org_id, config_file)
    try:
        with open(config_file_path) as f:
            return json.load(f)
            logging.info(f"Configuration loaded from {config_file_path}")
    except FileNotFoundError:
        return None
