# Get Secrets from env vars

$username = $env.USERNAME
$password = $env.PASSWORD
$credential_id = $env.CREDENTIAL_ID
$totp_secret = $env.TOTP_SECRET
$download_url = $env.DOWNLOAD_URL
$app_dist_path = $env.APP_DIST_PATH 

$input_file = "$app_dist_path\rewst_remote_agent.exe"
$output_file = "$app_dist_path\rewst_remote_agent_signed.exe"

# Download Code Sign Tool
Invoke-WebRequest -uri $download_url -OutFile codesigntool.zip
Expand-Archive -Path codesigntool.zip -DestinationPath .

$code_sign_folder = Get-ChildItem -Directory -Path . -Name CodeSign*
cd $code_sign_dir

# Sign Application
$sign_command = "$codeSignToolPath sign `
    -username=$username `
    -password=$password `
    -totp_secret=$totp_secret `
    -input_path=$input_file `
    -output_path=$output_file"

Invoke-Expression -Command $sign_command

# Check if the signing was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "Signing succeeded."
} else {
    Write-Host "Signing failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

# List Directory contents to see how things look
Get-ChildItem $app_dist_path

