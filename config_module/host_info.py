""" Module to get host info details """

from typing import Dict, Any

import platform
import uuid
import socket
import subprocess
import sys
import logging
import psutil
import __version__
from config_module.config_io import (
    get_service_executable_path,
    get_agent_executable_path,
)


def get_mac_address() -> str:
    """
    Get MAC Address of the host machine.

    Returns:
        str: MAC address in hexadecimal format iwhtout the columns.
    """
    # Use the psutil for hardware mac address
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                return str(addr.address).lower().replace("-", "")

    # Returns the MAC address of the host without colons
    mac_num = hex(uuid.UUID(int=uuid.getnode()).int)[2:]
    mac_address = ":".join(mac_num[i : i + 2] for i in range(0, 11, 2))
    return mac_address.replace(":", "")


def run_powershell_command(powershell_command: str) -> str | None:
    """
    Execute a powershell command and return the output

    Args:
        powershell_command (str): Powershell command to execute.

    Returns:
        str|None: Execution output if successful, otherwise None.
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", powershell_command],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing PowerShell script: {e}", file=sys.stderr)
        return None


def is_domain_controller() -> bool:
    """
    Checks if the current computer is a domain controller.

    Returns:
        bool: True if domain controller, otherwise False.
    """
    powershell_command = """
    $domainStatus = (Get-WmiObject Win32_ComputerSystem).DomainRole
    if ($domainStatus -eq 4 -or $domainStatus -eq 5) {
        return $true
    } else {
        return $false
    }
    """
    output = run_powershell_command(powershell_command)
    logging.info(f"Is domain controller?: {output}")
    return "True" in output


def get_ad_domain_name() -> str | None:
    """
    Gets the Active Directory domain name if the PC is joined to AD.

    Returns:
        str|None: Active directory domain name of the host if it exists, otherwise None.
    """

    powershell_command = """
    $domainInfo = (Get-WmiObject Win32_ComputerSystem).Domain
    if ($domainInfo -and $domainInfo -ne 'WORKGROUP') {
        return $domainInfo
    } else {
        return $null
    }
    """
    ad_domain_name = run_powershell_command(powershell_command)
    logging.info(f"AD domain name: {ad_domain_name}")
    return ad_domain_name


def get_entra_domain() -> str | None:
    """
    Get the Entra domain of the host machine.

    Returns:
        str|None: Entra domain if it exists, otherwise None.
    """
    if platform.system().lower() != "windows":
        return None
    else:
        try:
            result = subprocess.run(
                ["dsregcmd", "/status"], text=True, capture_output=True
            )
            output = result.stdout
            for line in output.splitlines():
                if "AzureAdJoined" in line and "YES" in line:
                    for line in output.splitlines():
                        if "DomainName" in line:
                            domain_name = line.split(":")[1].strip()
                            return domain_name
        except Exception as e:
            logging.warning(f"Unexpected issue querying for Entra Domain: {str(e)}")
            pass  # Handle exception if necessary
        return None


def is_entra_connect_server() -> bool:
    """
    Checks whether the host machine is an Entra connect server.

    Returns:
        bool: True if it is an Entra connect server, otherwise False.
    """
    if platform.system().lower() != "windows":
        return False
    else:
        potential_service_names = [
            "ADSync",
            "Azure AD Sync",
            "EntraConnectSync",
            "OtherFutureName",
        ]
        for service_name in potential_service_names:
            if is_service_running(service_name):
                return True
        return False


def is_service_running(service_name: str) -> bool:
    """
    Checks whether the service is running.

    Args:
        service_name (str): Service name to check.

    Returns:
        bool: True if the service is running, otherwise False.
    """
    for service in (
        psutil.win_service_iter()
        if platform.system() == "Windows"
        else psutil.process_iter(["name"])
    ):
        if service.name().lower() == service_name.lower():
            return True
    return False


def build_host_tags(org_id: str = None) -> Dict[str, Any]:
    """
    Build host tags for the organization.

    Args:
        org_id (str, optional): Organization identifier in Rewst platform. Defaults to None.

    Returns:
        Dict[str, Any]: Host tags detail.
    """
    # Collect host information
    ad_domain = get_ad_domain_name()
    if ad_domain:
        is_dc = is_domain_controller()
    else:
        is_dc = False

    host_info = {
        "agent_version": (__version__.__version__ or None),
        "agent_executable_path": get_agent_executable_path(org_id),
        "service_executable_path": get_service_executable_path(org_id),
        "hostname": socket.gethostname(),
        "mac_address": get_mac_address(),
        "operating_system": platform.platform(),
        "cpu_model": platform.processor(),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "ad_domain": ad_domain,
        "is_ad_domain_controller": is_dc,
        "is_entra_connect_server": is_entra_connect_server(),
        "entra_domain": get_entra_domain(),
        "org_id": org_id,
    }
    return host_info
