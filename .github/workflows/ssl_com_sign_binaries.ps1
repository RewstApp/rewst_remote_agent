# Get Secrets from env vars
$username = $env.USERNAME
$password = $env.PASSWORD
$credentialId = $env.CREDENTIAL_ID
$totpSecret = $env.TOTP_SECRET
$downloadUrl = $env.DOWNLOAD_URL
$appDistPath = $env.APP_DIST_PATH

$inputFile = "$appDistPath\rewst_remote_agent.exe"
$outputFile = "$appDistPath\rewst_remote_agent_signed.exe"

# Download Code Sign Tool
Write-Host "Downloading SSL.com Code Sign Tool from $downloadUrl"
Invoke-WebRequest -uri $downloadUrl -OutFile codesigntool.zip
Expand-Archive -Path codesigntool.zip -DestinationPath .

$codeSignDirectory = Get-ChildItem -Directory -Path . -Name CodeSign*
cd $codeSignDirectory

# Sign Application
$signCommand = ".\CodeSignTool.bat sign `
    -username=$username `
    -password=$password `
    -credential_id=$credentialId `
    -totpSecret=$totpSecret `
    -input_path=$inputFile `
    -output_path=$outputFile"

Invoke-Expression -Command $signCommand

# Check if the signing was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "Signing succeeded."
} else {
    Write-Host "Signing failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

# Get App Dist Directory Contents
Get-ChildItem $appDistPath

