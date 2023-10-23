@echo off
pyinstaller --icon=logo-rewsty.ico --onefile rewst_remote_agent.py config_module.py service_manager.py

