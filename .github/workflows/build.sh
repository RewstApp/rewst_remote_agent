#!/bin/bash

# Build the first executable
pyinstaller --name=rewst_remote_agent  --one-file --icon=logo-rewsty.ico --version-file=version.txt rewst_remote_agent.py

# Build the second executable
pyinstaller --name=rewst_service_manager --one-file --icon=logo-rewsty.ico --version-file=version.txt rewst_service_manager.py

# Build the third executable
pyinstaller --name=rewst_agent_config --one-file --icon=logo-rewsty.ico --version-file=version.txt rewst_agent_config.py
