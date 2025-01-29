param(
    [string]$username,
    [string]$password,
    [string]$credentialId,
    [string]$totpSecret
)

$downloadUrl = 'https://www.ssl.com/download/codesigntool-for-windows/'
$appDistPath =  'D:\a\rewst_remote_agent\rewst_remote_agent\dist'

$inputFiles = @(
    "rewst_agent_config.exe",
    "rewst_service_manager.exe",
    "rewst_windows_service.exe",
    "rewst_remote_agent.exe"
)
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
Write-Host "codeSignDirectory contents:"
dir $codeSignDirectory

##  Uncomment when faking it
# Set-Location $codeSignDirectory


# Sign Application
foreach ($inputFile in $inputFiles) {
    Write-Host "Signing $inputFile"
    $signArguments = @(
        "sign",
        "-username=$username",
        "-password=$password",
        "-credential_id=$credentialId",
        "-totp_secret=$totpSecret",
        "-input_file_path=$appDistPath\$inputFile",
        "-output_dir_path=$outputDirPath"
    )

    ## Uncomment this to sign for reals
    Start-Process -FilePath ".\CodeSignTool.bat" -ArgumentList $signArguments -Wait -NoNewWindow
    Write-Host "Signed to $outputDirPath\$inputFile"


    ## UnComment these to do fake sign
    Write-Host "Faking it: Signed to $outputDirPath\$inputFile"
    Copy-Item $appDistPath\$inputFile $outputDirPath

    
}


#Check if the signing was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "Signing succeeded."
} else {
    Write-Host "Signing failed with exit code $LASTEXITCODE."
}

# Get App Dist Directory Contents
Write-Host "appDistPath ($appDistPath) Contents:"
Get-ChildItem $appDistPath

Write-Host "Signed Folder ($outputDirPath) Contents:"
Get-ChildItem $outputDirPath

