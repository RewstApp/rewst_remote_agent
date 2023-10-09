#!/bin/sh

dnf -y install wine curl

curl -o python-3.11.6-amd64.exe 'https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe'

wine msiexec /i python-3.11.6-amd64.exe

wine python.exe ~/.wine/drive_c/Python311/Scripts/pip.exe install pyinstaller

wine ~/.wine/drive_c/Python311/Scripts/pyinstaller --onefile rewst_remote_agent.exe
