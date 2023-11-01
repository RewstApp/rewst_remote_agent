@echo off
pyinstaller --icon=logo-rewsty.ico --version-file=version.txt --onefile rewst_remote_agent.py config_module.py service_manager.py __version__.py
