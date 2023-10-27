import asyncio
import logging
import platform
import os
import shutil
import time
from config_module import get_config_file_path, load_configuration

os_type = platform.system()

# Put Timestamps on logging entries
logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

if os_type == "Windows":
    import win32service
    import win32serviceutil
    import win32event

class RewstService(win32serviceutil.ServiceFramework):

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        config_data = load_configuration()  # Load the configuration
        self.org_id = config_data.get('rewst_org_id')

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        asyncio.run(main(org_id=self.org_id))  # pass org_id to the main function

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        stop_event.set()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

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
    

def get_executable_path(org_id):
    if os_type == "Windows":
        program_files_dir = os.environ.get('ProgramFiles')  # This will get the path to Program Files directory
        executable_path = os.path.join(program_files_dir, f"RewstRemoteAgent\\{org_id}\\rewst_remote_agent_{org_id}.win.exe")
    elif os_type == "Linux":
        executable_path = f"/usr/local/bin/rewst_remote_agent_{org_id}.linux.bin"
    elif os_type == "Darwin":
        executable_path = os.path.expanduser(f"~/Library/Application Support/RewstRemoteAgent/rewst_remote_agent_{org_id}.macos.bin")
    return executable_path


def install_binaries(org_id):
    # Copy the executable to the appropriate location
    executable_path = get_executable_path(org_id)
    logging.info(f"Writing executable to {executable_path}")
    
    # Create missing directories
    directory = os.path.dirname(executable_path)
    os.makedirs(directory, exist_ok=True)
    
    # Copy executable
    if os_type == "Windows":
        shutil.copy("rewst_remote_agent.win.exe", executable_path)
    elif os_type == "Linux":
        shutil.copy("rewst_remote_agent.linux.bin", executable_path)
    elif os_type == "Darwin":
        shutil.copy("rewst_remote_agent.macos.bin", executable_path)


def install_service(org_id, config_file=None):
    executable_path = get_executable_path(org_id)
    service_name = get_service_name(org_id)
    # Uninstall the service if it's already installed
    if is_service_installed(org_id):
        logging.info(f"Service is already installed. Reinstalling service.")
        uninstall_service(org_id)
        # Wait for the service to be deleted
        while is_service_installed(service_name):
            time.sleep(2)  # wait for 2 seconds
    
    display_name = f"Rewst Remote Agent {org_id}"
    config_file_path = get_config_file_path(org_id,config_file)

    # Install the service
    if os_type == "Windows":
        import win32serviceutil
        win32serviceutil.InstallService(
            f"{RewstService.__module__}.{RewstService.__name__}",
            service_name,
            displayName=display_name,
            startType=win32service.SERVICE_AUTO_START,
            exeName=sys.executable,
            args=[get_executable_path(org_id), f'--config-file {config_file_path}']
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
        os.system(f"launchctl load {plist_path}")

def uninstall_service(org_id):
    service_name = get_service_name(org_id)
    logging.info(f"Uninstalling service {service_name}.")

    stop_service(org_id)
         
    if os_type == "Windows":
        import win32serviceutil
        win32serviceutil.RemoveService(service_name)
    elif os_type == "Linux":
        os.system(f"systemctl disable {service_name}")
        os.system(f"rm /etc/systemd/system/{service_name}.service")
        os.system("systemctl daemon-reload")
    elif os_type == "Darwin":
        plist_path = f"{os.path.expanduser('~/Library/LaunchAgents')}/{service_name}.plist"
        os.system(f"launchctl unload {plist_path}")
        os.system(f"rm {plist_path}")

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
        try:
            win32serviceutil.StopService(service_name)
        except pywintypes.error as e:
            # handle any exceptions as needed, for example:
            if e.winerror != winerror.ERROR_SERVICE_DOES_NOT_EXIST:
                raise            
        os.system(f"net stop {service_name}")
    elif os_type == "Linux":
        os.system(f"systemctl stop {service_name}")
    elif os_type == "Darwin":
        os.system(f"launchctl stop {service_name}")


def restart_service(org_id):
    stop_service(org_id)
    start_service(org_id)
