import platform
import socket
import uuid
import psutil
import subprocess
import logging

def get_mac_address():
    # Returns the MAC address of the host without colons
    mac_num = hex(uuid.UUID(int=uuid.getnode()).int)[2:]
    mac_address = ':'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
    return mac_address.replace(':', '')


def is_domain_controller():
    if platform.system().lower() != 'windows':
        return False
    else:
        domain_name = get_ad_domain_name()
        if domain_name is None:
            return False
        try:
            result = subprocess.run([f'nltest', f'/dclist:{domain_name}'], text=True, capture_output=True, check=True)
            domain_controllers = result.stdout.split('\n')
            local_machine = socket.gethostname()
            return any(local_machine in dc for dc in domain_controllers)
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed with error: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return False


def get_ad_domain_name():
    if platform.system().lower() != 'windows':
        return None
    else:
        try:
            result = subprocess.run(['dsregcmd', '/status'], text=True, capture_output=True, check=True)
            for line in result.stdout.split('\n'):
                if 'Domain Name' in line:
                    return line.split(':')[1].strip()
            logging.warning("Domain Name not found in dsregcmd output. This is expected if the computer is not domain-joined.")
            return None
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed with error: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return None


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
