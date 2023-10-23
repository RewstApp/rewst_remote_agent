import platform
import os
import shutil

os_type = platform.system()

if os_type == "Windows":
    import win32service
    import win32serviceutil

def get_service_name(org_id):
    return f"Rewst_Remote_Agent_{org_id}"

def get_executable_path(org_id):
    if os_type == "Windows":
        executable_path = os.path.expanduser(f"~\\AppData\\Local\\RewstRemoteAgent\\rewst_remote_agent_{org_id}.win.exe")
    elif os_type == "Linux":
        executable_path = f"/usr/local/bin/rewst_remote_agent_{org_id}.linux.bin"
    elif os_type == "Darwin":
        executable_path = os.path.expanduser(f"~/Library/Application Support/RewstRemoteAgent/rewst_remote_agent_{org_id}.macos.bin")
    return executable_path

def install_service(org_id):
    service_name = get_service_name(org_id)
    executable_path = get_executable_path(org_id)
    display_name = f"Rewst Remote Agent {org_id}"

    # Copy the executable to the appropriate location
    if os_type == "Windows":
        shutil.copy("rewst_remote_agent.win.exe", executable_path)
    elif os_type == "Linux":
        shutil.copy("rewst_remote_agent.linux.bin", executable_path)
    elif os_type == "Darwin":
        shutil.copy("rewst_remote_agent.macos.bin", executable_path)

    # Install the service
    if os_type == "Windows":
        import win32serviceutil
        win32serviceutil.InstallService(
            executable_path,
            service_name,
            displayName=display_name
            startType=win32service.SERVICE_AUTO_START
        )
    elif os_type == "Linux":
        systemd_service_content = f"""
        [Unit]
        Description={service_name}

        [Service]
        ExecStart={executable_path}
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
    if os_type == "Windows":
        os.system(f"net start {service_name}")
    elif os_type == "Linux":
        os.system(f"systemctl start {service_name}")
    elif os_type == "Darwin":
        os.system(f"launchctl start {service_name}")
   

def stop_service(org_id):
    service_name = get_service_name(org_id)
    if os_type == "Windows":
        os.system(f"net stop {service_name}")
    elif os_type == "Linux":
        os.system(f"systemctl stop {service_name}")
    elif os_type == "Darwin":
        os.system(f"launchctl stop {service_name}")


def restart_service(org_id):
    stop_service(org_id)
    start_service(org_id)
