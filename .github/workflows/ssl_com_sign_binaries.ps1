param(
    [string]$username,
    [string]$password,
    [string]$credentialId,
    [string]$totpSecret
)

$downloadUrl = 'https://www.ssl.com/download/codesigntool-for-windows/'
$appDistPath =  'D:\a\rewst_remote_agent\rewst_remote_agent\dist'

$inputFile = "$appDistPath\rewst_remote_agent.exe"
$outputDirPath = "$appDistPath\signed"

write-host "Signing App as Username: $username"

New-Item -Type Directory $outputDirPath

Write-Host "App Distribution Directory Contents:"
Get-ChildItem $appDistPath

# Download Code Sign Tool
try {
    Invoke-WebRequest -uri $downloadUrl -OutFile codesigntool.zip
    Expand-Archive -Path codesigntool.zip -DestinationPath .
} catch {
    Write-Host "Error: $_"
    exit 1
}

$codeSignDirectory = Get-ChildItem -Directory -Path . -Name CodeSign*
Set-Location $codeSignDirectory

# Sign Application
$signArguments = @(
    "sign",
    "-username=$username",
    "-password=$password",
    "-credential_id=$credentialId",
    "-totp_secret=$totpSecret",
    "-input_file_path=$inputFile",
    "-output_dir_path=$outputDirPath"

Start-Process -FilePath ".\CodeSignTool.bat" -ArgumentList $signArguments -Wait -NoNewWindow

# Check if the signing was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "Signing succeeded."
} else {
    Write-Host "Signing failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

# Get App Dist Directory Contents
Write-Host "App Distribution Directory Contents:"
Get-ChildItem -Recursive $appDistPath

