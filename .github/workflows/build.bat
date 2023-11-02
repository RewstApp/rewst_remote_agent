@echo off
REM Build the first executable
pyinstaller --name=rewst_remote_agent --icon=logo-rewsty.ico --version-file=version.txt rewst_remote_agent.py

REM Build the second executable
pyinstaller --name=rewst_service_manager --icon=logo-rewsty.ico --version-file=version.txt rewst_service_manager.py

REM Build the third executable
pyinstaller --name=rewst_agent_config --icon=logo-rewsty.ico --version-file=version.txt rewst_agent_config.py
