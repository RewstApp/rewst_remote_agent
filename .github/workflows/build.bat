@echo off
REM Explicitly include the pywin32 module
SET PYWIN32_INCLUDE=--hidden-import=pywin32

REM Build the first executable with hidden imports
pyinstaller %PYWIN32_INCLUDE% --name=rewst_remote_agent --icon=logo-rewsty.ico --onefile --version-file=version.txt rewst_remote_agent.py

REM Build the second executable with hidden imports
pyinstaller %PYWIN32_INCLUDE% --name=rewst_service_manager --icon=logo-rewsty.ico --onefile --version-file=version.txt rewst_service_manager.py

REM Build the third executable with hidden imports
pyinstaller %PYWIN32_INCLUDE% --name=rewst_agent_config --icon=logo-rewsty.ico --onefile --version-file=version.txt rewst_agent_config.py
