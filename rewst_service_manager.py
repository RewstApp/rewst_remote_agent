import argparse
import asyncio
import logging
import os
import platform
import subprocess
from config_module import (
    config_io
)


os_type = platform.system()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

if os_type == "Windows":
    import win32service
    import win32serviceutil
    import win32event
    import pywintypes

class RewstService(win32serviceutil.ServiceFramework):
    _svc_name_ = None  # Placeholder, will be set in __init__
    _svc_display_name_ = None  # Placeholder, will be set in __init__

    # Defining stop_event as a class variable
    stop_event = asyncio.Event()

    def __init__(self, args):
        super().__init__(args)
        config_data = config_io.load_configuration()  # Load the configuration
        self.org_id = config_data.get('rewst_org_id')
        self.set_service_name(self.org_id)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    @classmethod
    def set_service_name(cls, org_id):
        cls._svc_name_ = get_service_name(org_id)
        cls._svc_display_name_ = f"Rewst Remote Service {org_id}"

    def SvcDoRun(self):
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)  # Report service as running
            asyncio.run(main(org_id=self.org_id, stop_event=RewstService.stop_event))  # pass stop_event to main
        except Exception as e:
            logging.error(f"Exception in SvcDoRun: {e}")
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)  # Report service as stopped if there's an error

    def SvcStop(self):
        try:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)  # Report service as stopping
            RewstService.stop_event.set()  # Set stop_event to signal the service to stop
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)  # Report service as stopped
        except Exception as e:
            logging.error(f"Exception in SvcStop: {e}")

def get_service_name(org_id):
    return f"Rewst_Remote_Agent_{org_id}"


def is_service_installed(org_id=None):
    service_name = get_service_name(org_id)
    if os_type == "Windows":
        import win32serviceutil
        try:
            win32serviceutil.QueryServiceStatus(service_name)
            return True  # Service is installed
        except Exception as e:
            return False  # Service is not installed
    elif os_type == "Linux":
        service_path = f"/etc/systemd/system/{service_name}.service"
        return os.path.exists(service_path)
    elif os_type == "Darwin":
        plist_path = f"{os.path.expanduser('~/Library/LaunchAgents')}/{service_name}.plist"
        return os.path.exists(plist_path)


def install_service(org_id, config_file=None):
    executable_path = config_io.get_executable_path(org_id)
    service_name = get_service_name(org_id)
    display_name = f"Rewst Remote Agent {org_id}"
    if is_service_installed(org_id):
        logging.info(f"Service is already installed.")
        return
    
    config_file_path = get_config_file_path(org_id, config_file)

    # Install the service
    if os_type == "Windows":
        logging.info(f"Installing Windows Service: {service_name}")
        win32serviceutil.InstallService(
            f"{RewstService.__module__}.{RewstService.__name__}",
            service_name,
            displayName=display_name,
            startType=win32service.SERVICE_AUTO_START,
            exeName=executable_path
        )

    elif os_type == "Linux":
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
        os.system("systemctl daemon-reload")
        os.system(f"systemctl enable {service_name}")
    
    elif os_type == "Darwin":
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
        with open(f"{os.path.expanduser('~/Library/LaunchAgents')}/{service_name}.plist", "w") as f:
            f.write(launchd_plist_content)
        os.system(f"launchctl load {service_name}")

def uninstall_service(org_id):
    service_name = get_service_name(org_id)
    logging.info(f"Uninstalling service {service_name}.")

    try:
        stop_service(org_id)
    except Exception as e:
        logging.warning(f"Unable to stop service: {e}")
         
    if os_type == "Windows":
        import win32serviceutil
        try:
            win32serviceutil.RemoveService(service_name)
        except Exception as e:
            logging.warning(f"Exception removing service: {e}")
    
    elif os_type == "Linux":
        os.system(f"systemctl disable {service_name}")
        os.system(f"rm /etc/systemd/system/{service_name}.service")
        os.system("systemctl daemon-reload")
    
    elif os_type == "Darwin":
        plist_path = f"{os.path.expanduser('~/Library/LaunchAgents')}/{service_name}.plist"
        os.system(f"launchctl unload {plist_path}")
        os.system(f"rm {plist_path}")


def check_service_status(org_id):
    service_name = get_service_name(org_id)
    
    if os_type == "Windows":
        import win32serviceutil
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            print(f'Service status: {status[1]}')  # Printing the status to stdout
        except Exception as e:
            print(f'Error: {e}')
    
    elif os_type == "Linux":
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], 
                                    text=True, capture_output=True, check=True)
            print(f'Service status: {result.stdout.strip()}')
        except subprocess.CalledProcessError as e:
            print(f'Error: {e.stdout.strip()}')
        except Exception as e:
            print(f'Error: {e}')
    
    elif os_type == "Darwin":
        try:
            result = subprocess.run(['launchctl', 'list', service_name], 
                                    text=True, capture_output=True, check=True)
            if f"{service_name}" in result.stdout:
                print(f'Service status: Running')
            else:
                print(f'Service status: Not Running')
        except subprocess.CalledProcessError as e:
            print(f'Error: {e.stdout.strip()}')
        except Exception as e:
            print(f'Error: {e}')

    else:
        print(f'Unsupported OS type: {os_type}')


def start_service(org_id):
    service_name = get_service_name(org_id)
    logging.info(f"Starting Service {service_name}")
    if os_type == "Windows":
        os.system(f"net start {service_name}")
    elif os_type == "Linux":
        os.system(f"systemctl start {service_name}")
    elif os_type == "Darwin":
        os.system(f"launchctl start {service_name}")

def stop_service(org_id):
    service_name = get_service_name(org_id)
    if os_type == "Windows":
        if win32serviceutil.QueryServiceStatus(service_name):
            try:
                win32serviceutil.StopService(service_name)
            except pywintypes.error as e:
                logging.error(f"Failed to stop service: {e.strerror}") 
    elif os_type == "Linux":
        os.system(f"systemctl stop {service_name}")
    elif os_type == "Darwin":
        os.system(f"launchctl stop {service_name}")

def restart_service(org_id):
    stop_service(org_id)
    start_service(org_id)


def main():
    parser = argparse.ArgumentParser(description='Rewst Service Manager.')
    parser.add_argument('--org-id', required=True, help='Organization ID')
    parser.add_argument('--config-file', help='Path to the configuration file')
    parser.add_argument('--install', action='store_true', help='Install the service')
    parser.add_argument('--uninstall', action='store_true', help='Uninstall the service')
    parser.add_argument('--status', action='store_true', help='Check the service status')
    parser.add_argument('--start', action='store_true', help='Start the service')
    parser.add_argument('--stop', action='store_true', help='Stop the service')
    parser.add_argument('--restart', action='store_true', help='Restart the service')

    args = parser.parse_args()

    # Load configuration if config file path is provided
    if args.config_file:
        config_io.load_from_file(args.config_file)

    # Set the service name based on the organization ID
    RewstService.set_service_name(args.org_id)

    # Perform the requested service action
    if args.install:
        install_service(args.org_id, args.config_file)
    elif args.uninstall:
        uninstall_service(args.org_id)
    elif args.start:
        start_service(args.org_id)
    elif args.stop:
        stop_service(args.org_id)
    elif args.restart:
        restart_service(args.org_id)
    else:
        print("No action specified. Use --install, --uninstall, --start, --stop, or --restart.")

if __name__ == "__main__":
    main()
