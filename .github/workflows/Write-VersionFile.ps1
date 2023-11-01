param(
    [string]$version
)

$formatted_version = "$version" -replace '\.', ','

$versionInfo = @"
VSVersionInfo(
    ffi=FixedFileInfo(
      filevers=($formatted_version,0),
      prodvers=($formatted_version,0),
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