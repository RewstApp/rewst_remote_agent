import platform

os_type = platform.system()




def install_service():
    if os_type == "Windows":
        # For Windows, using pywin32
        import win32serviceutil
        win32serviceutil.InstallService(
            "rewst_remote_agent.exe",  # Your script
            "Rewst_Remote_Agent",  # Service name
            startType=win32service.SERVICE_AUTO_START
        )
    elif os_type == "Linux":
        # For Linux, using systemd
        systemd_service_content = f"""
        [Unit]
        Description=RewstRemoteAgent

        [Service]
        ExecStart={os.path.abspath(__file__)}
        Restart=always

        [Install]
        WantedBy=multi-user.target
        """
        with open("/etc/systemd/system/rewst_remote_agent.service", "w") as f:
            f.write(systemd_service_content)
        os.system("systemctl daemon-reload")
        os.system("systemctl enable rewst_remote_agent")
    elif os_type == "Darwin":
        # For macOS, using launchd
        launchd_plist_content = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.rewst_remote_agent</string>
            <key>ProgramArguments</key>
            <array>
                <string>{os.path.abspath(__file__)}</string>
            </array>
            <key>RunAtLoad</key>
            <true/>
        </dict>
        </plist>
        """
        with open(f"{os.path.expanduser('~')}/Library/LaunchAgents/com.rewst_remote_agent.plist", "w") as f:
            f.write(launchd_plist_content)
