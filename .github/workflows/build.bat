@echo off
REM Explicitly include the pywin32 module
SET PYWIN32_INCLUDE=--hidden-import=pywin32

REM pyinstaller %PYWIN32_INCLUDE% --name=rewst_remote_agent --icon=logo-rewsty.ico --onefile --version-file=version.txt rewst_remote_agent.py

pyinstaller %PYWIN32_INCLUDE% --name=rewst_service_manager --icon=logo-rewsty.ico --onefile --version-file=version.txt rewst_service_manager.py

pyinstaller %PYWIN32_INCLUDE% --name=rewst_agent_config --icon=logo-rewsty.ico --onefile --version-file=version.txt rewst_agent_config.py

pyinstaller %PYWIN32_INCLUDE% --name=rewst_agent_config --icon=logo-rewsty.ico --onefile --version-file=version.txt rewst_windows_service.py
