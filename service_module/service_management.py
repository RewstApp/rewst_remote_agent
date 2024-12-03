""" Module providing helper functions to manage an agent service. """

import logging
import os
import platform
import subprocess
import psutil
from config_module.config_io import (
    get_agent_executable_path,
    get_config_file_path,
    get_service_executable_path,
)

os_type = platform.system().lower()

if os_type == "windows":
    import win32service
    import win32serviceutil
    import pywintypes
    from rewst_windows_service import RewstWindowsService


def get_service_name(org_id: str) -> str:
    """
    Get the current service name of the using the latest platform.

    Args:
        org_id (str): Organization identifier in Rewst platform.

    Returns:
        str: Service name of the agent.
    """
    if os_type == "windows":
        # Fetch the service name from the RewstWindowsService class
        return RewstWindowsService.get_service_name()
    else:
        # Construct the service name for non-Windows operating systems
        return f"RewstRemoteAgent_{org_id}"


def is_service_installed(org_id: str = None) -> bool:
    """
    Checks whether the agent service for an organization is installed or not.

    Args:
        org_id (str, optional): Organization identifier in Rewst platform. Defaults to None.

    Returns:
        bool: True if installed, otherwise False.
    """
    service_name = get_service_name(org_id)
    if os_type == "windows":
        try:
            win32serviceutil.QueryServiceStatus(service_name)
            logging.info(f"Service {service_name} is installed.")
            return True  # Service is installed
        except Exception as e:
            logging.exception(f"Error returning service information: {e}")
            return False  # Service is not installed
    elif os_type == "linux":
        service_path = f"/etc/systemd/system/{service_name}.service"
        logging.info(f"Service {service_name} is installed.")
        return os.path.exists(service_path)
    elif os_type == "darwin":
        plist_path = (
            f"{os.path.expanduser('~/Library/LaunchAgents')
               }/{service_name}.plist"
        )
        logging.info(f"Service {service_name} is installed.")
        return os.path.exists(plist_path)


def is_service_running(org_id: str = None) -> bool|str:
    """
    Checks whether the agent service for an organization is running or not.

    Args:
        org_id (str, optional): Organization identifier in Rewst platform. Defaults to None.

    Returns:
        bool|str: Executable name as string if running, otherwise False.
    """
    executable_path = get_agent_executable_path(org_id)
    executable_name = os.path.basename(executable_path)
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"] == executable_name:
            return executable_name
    return False


def install_service(org_id: str) -> None:
    """
    Installs the agent service for an organization.

    Args:
        org_id (str): Organization identifier in Rewst platform.
    """
    executable_path = get_agent_executable_path(org_id)
    service_name = get_service_name(org_id)

    logging.info(f"Installing {service_name} Service...")
    config_file_path = get_config_file_path(org_id)
    if is_service_installed(org_id):
        logging.info(f"Service is already installed.")
    else:
        if os_type == "windows":
            logging.info(f"Installing Windows Service: {service_name}")
            # install using service executable
            windows_service_path = get_service_executable_path(org_id)
            subprocess.run(([windows_service_path, "install"]))

        elif os_type == "linux":
            systemd_service_content = f"""
            [Unit]
            Description={service_name}

            [Service]
            ExecStart={executable_path} --config-file {config_file_path}
            Restart=always

            [Install]
            WantedBy=multi-user.target
            """
            with open(f"/etc/systemd/system/{service_name}.service", "w") as f:
                f.write(systemd_service_content)
            subprocess.run("systemctl daemon-reload")
            subprocess.run(f"systemctl enable {service_name}")

        elif os_type == "darwin":
            launchd_plist_content = f"""
            <?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
            <plist version="1.0">
            <dict>
                <key>Label</key>
                <string>{service_name}</string>
                <key>ProgramArguments</key>
                <array>
                    <string>{executable_path}</string>
                    <string>--config-file</string>
                    <string>{config_file_path}</string>
                </array>
                <key>RunAtLoad</key>
                <true/>
            </dict>
            </plist>
            """
            with open(
                f"{os.path.expanduser('~/Library/LaunchAgents')
                   }/{service_name}.plist",
                "w",
            ) as f:
                f.write(launchd_plist_content)
            subprocess.run(f"launchctl load {service_name}")


def uninstall_service(org_id: str) -> None:
    """
    Uninstalls an agent service for an organization.

    Args:
        org_id (str): Organization identifier in Rewst platform.
    """

    service_name = get_service_name(org_id)
    logging.info(f"Uninstalling service {service_name}.")

    try:
        stop_service(org_id)
    except Exception as e:
        logging.warning(f"Unable to stop service: {e}")

    if os_type == "windows":
        try:
            win32serviceutil.RemoveService(service_name)
        except Exception as e:
            logging.warning(f"Exception removing service: {e}")

    elif os_type == "linux":
        subprocess.run(f"systemctl disable {service_name}")
        subprocess.run(f"rm /etc/systemd/system/{service_name}.service")
        subprocess.run("systemctl daemon-reload")

    elif os_type == "darwin":
        plist_path = (
            f"{os.path.expanduser('~/Library/LaunchAgents')
               }/{service_name}.plist"
        )
        subprocess.run(f"launchctl unload {plist_path}")
        subprocess.run(f"rm {plist_path}")


def check_service_status(org_id: str) -> None:
    """
    Prints the status of an agent service for an organization to stdout.

    Args:
        org_id (str): Organization identifier in Rewst platform.
    """
    service_name = get_service_name(org_id)

    if os_type == "windows":
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            # Printing the status to stdout
            print(f"Service status: {status[1]}")
        except Exception as e:
            print(f"Error: {e}")

    elif os_type == "linux":
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                text=True,
                capture_output=True,
                check=True,
            )
            print(f"Service status: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stdout.strip()}")

        except Exception as e:
            print(f"Error: {e}")

    elif os_type == "darwin":
        try:
            result = subprocess.run(
                ["launchctl", "list", service_name],
                text=True,
                capture_output=True,
                check=True,
            )
            if f"{service_name}" in result.stdout:
                print(f"Service status: Running")
            else:
                print(f"Service status: Not Running")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stdout.strip()}")
        except Exception as e:
            print(f"Error: {e}")

    else:
        print(f"Unsupported OS type: {os_type}")


def start_service(org_id: str) -> None:
    """
    Start the agent service for an organization.

    Args:
        org_id (str): Organization identifier in Rewst platform.
    """
    service_name = get_service_name(org_id)
    logging.info(f"Starting Service {service_name} for {os_type}")
    if os_type == "windows":
        win32serviceutil.StartService(service_name)
    elif os_type == "linux":
        subprocess.run(f"systemctl start {service_name}")
    elif os_type == "darwin":
        subprocess.run(f"launchctl start {service_name}")


def stop_service(org_id: str) -> None:
    """
    Stop the agent service for an organization.

    Args:
        org_id (str): Organization identifier in Rewst platform.
    """
    service_name = get_service_name(org_id)
    if os_type == "windows":
        if win32serviceutil.QueryServiceStatus(service_name):
            try:
                win32serviceutil.StopService(service_name)
            except pywintypes.error as e:
                logging.error(f"Failed to stop service: {e.strerror}")
    elif os_type == "linux":
        subprocess.run(f"systemctl stop {service_name}")
    elif os_type == "darwin":
        subprocess.run(f"launchctl stop {service_name}")


def restart_service(org_id: str) -> None:
    """
    Restart the agent service for an organization.

    Args:
        org_id (str): Organization identifier in Rewst platform.
    """
    stop_service(org_id)
    start_service(org_id)
