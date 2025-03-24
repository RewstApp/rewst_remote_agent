Write-Host "Building agent config..."
poetry run python ./scripts/windows_version_file.py > ./version.txt
poetry run pyinstaller --hidden-import win32timezone --icon=assets/logo-rewsty.ico --onefile rewst_windows_service.py --version-file=./version.txt