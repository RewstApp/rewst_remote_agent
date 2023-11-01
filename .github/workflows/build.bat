@echo off
pyinstaller --icon=logo-rewsty.ico --version-file=__version__.py --onefile rewst_remote_agent.py config_module.py service_manager.py

