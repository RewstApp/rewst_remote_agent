""" Utility program to write the version file for the windows compiled assets """
from __version__ import __version__

NUM_SEPARATORS = 3

def main() -> None:
    """
    Main entry point of the program
    """
    formatted_version = __version__.replace('.', ',')

    # Append the formatted version so that it will have four numbers: #,#,#,#
    while formatted_version.count(",") < NUM_SEPARATORS:
        formatted_version += ',0'

    # Build the version file
    version_file = f"""VSVersionInfo(
        ffi=FixedFileInfo(
        filevers=({formatted_version}),
        prodvers=({formatted_version}),
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
                [StringStruct(u'FileVersion', u'{__version__}'),
                StringStruct(u'ProductVersion', u'{__version__}')]
            )
            ]
        ),
        VarFileInfo([VarStruct(u'Translation', [0x409, 1200])])
        ]
    )"""

    print(version_file)

if __name__ == '__main__':
    main()
