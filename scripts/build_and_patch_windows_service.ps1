param(
    [string]$orgId
)

if ("" -eq $orgId) {
    Write-Host "Missing param orgId."
    exit 1
}

$builtWindowsServicePath = "./dist/rewst_windows_service.exe"
$targetWindowsServicePath = "C:\Program Files\RewstRemoteAgent\$orgId\rewst_windows_service_$orgId.win.exe"

Remove-Item $builtWindowsServicePath -ErrorAction SilentlyContinue
Write-Host "Removed file $builtWindowsServicePath."

Remove-Item $targetWindowsServicePath -ErrorAction SilentlyContinue
Write-Host "Removed file $targetWindowsServicePath."

Write-Host "Building windows service..."
poetry run python ./scripts/windows_version_file.py > ./version.txt
poetry run pyinstaller --hidden-import win32timezone --icon=assets/logo-rewsty.ico --onefile rewst_windows_service.py --version-file=./version.txt

Copy-Item $builtWindowsServicePath -Destination $targetWindowsServicePath
Write-Host "Copied file $builtWindowsServicePath to $targetWindowsServicePath."
