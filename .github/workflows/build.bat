@echo off
pyinstaller --onefile rewst_remote_agent.py --icon=logo-rewsty.ico config_module.py service_manager.py

