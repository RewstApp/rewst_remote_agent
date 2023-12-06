import platform
import uuid
import psutil
import socket
import subprocess
import sys
import logging
import __version__
from config_module.config_io import (
    get_service_executable_path,
    get_agent_executable_path
)


def get_mac_address():
    # Returns the MAC address of the host without colons
    mac_num = hex(uuid.UUID(int=uuid.getnode()).int)[2:]
    mac_address = ':'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
    return mac_address.replace(':', '')


def run_powershell_command(powershell_command):
    """Executes a PowerShell command and returns the output."""
    try:
        result = subprocess.run(["powershell", "-Command", powershell_command], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing PowerShell script: {e}", file=sys.stderr)
        return None


def is_domain_controller():
    """Checks if the current computer is a domain controller."""
    powershell_command = """
    try {
        Import-Module ActiveDirectory -ErrorAction Stop
        $dc = Get-ADDomainController -Identity $env:COMPUTERNAME
        if ($dc) { return $true }
        else { return $false }
    } catch {
        return $false
    }
    """
    output = run_powershell_command(powershell_command)
    return 'True' in output


def get_ad_domain_name():
    """Gets the Active Directory domain name."""
    powershell_command = """
    try {
        $domain = (Get-ADDomain).Name
        if ($domain) { return $domain }
        else { return $null }
    } catch {
        return $null
    }
    """
    return run_powershell_command(powershell_command)


def get_entra_domain():
    if platform.system().lower() != 'windows':
        return None
    else:
        try:
            result = subprocess.run(['dsregcmd', '/status'], text=True, capture_output=True)
            output = result.stdout
            for line in output.splitlines():
                if 'AzureAdJoined' in line and 'YES' in line:
                    for line in output.splitlines():
                        if 'DomainName' in line:
                            domain_name = line.split(':')[1].strip()
                            return domain_name
        except Exception as e:
            logging.warning(f"Unexpected issue querying for Entra Domain: {str(e)}")
            pass  # Handle exception if necessary
        return None


def is_entra_connect_server():
    if platform.system().lower() != 'windows':
        return False
    else:
        potential_service_names = ["ADSync", "Azure AD Sync", "EntraConnectSync", "OtherFutureName"]
        for service_name in potential_service_names:
            if is_service_running(service_name):
                return True
        return False


def is_service_running(service_name):
    for service in psutil.win_service_iter() if platform.system() == 'Windows' else psutil.process_iter(['name']):
        if service.name().lower() == service_name.lower():
            return True
    return False


def build_host_tags(org_id=None):
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
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
        "ad_domain": ad_domain,
        "is_ad_domain_controller": is_dc,
        "is_entra_connect_server": is_entra_connect_server(),
        "entra_domain": get_entra_domain(),
        "org_id": org_id
    }
    return host_info
