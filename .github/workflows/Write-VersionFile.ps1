param(
    [string]$version
)

# Ensure the version string contains exactly three values separated by commas
$formatted_version = "$version" -replace '\.', ',' -replace '-service-refactor', ''
$version_parts = $formatted_version.Split(',')
while ($version_parts.Count -lt 4) {
    $formatted_version += ',0'
}

$versionInfo = @"
VSVersionInfo(
    ffi=FixedFileInfo(
      filevers=($formatted_version),
      prodvers=($formatted_version),
      mask=0x3f,
      flags=0x0,
      OS=0x4,
      fileType=0x1,
      subtype=0x0,
      date=(0, 0)
    ),
    kids=[
      StringFileInfo(
        [
          StringTable(
            u'040904b0',
            [StringStruct(u'FileVersion', u'$version'),
            StringStruct(u'ProductVersion', u'$version')]
          )
        ]
      ),
      VarFileInfo([VarStruct(u'Translation', [0x409, 1200])])
    ]
  )
"@

$versionInfo | Out-File -FilePath version.txt -Encoding utf8

Get-Content -Path version.txt