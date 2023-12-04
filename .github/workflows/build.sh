#!/bin/bash

# Build the first executable
pyinstaller --name=rewst_remote_agent  --onefile --icon=logo-rewsty.ico --version-file=version.txt rewst_remote_agent.py

# Build the second executable
pyinstaller --name=rewst_service_manager --onefile --icon=logo-rewsty.ico --version-file=version.txt rewst_service_manager.py

# Build the third executable
pyinstaller --name=rewst_agent_config --onefile --icon=logo-rewsty.ico --version-file=version.txt rewst_agent_config.py
