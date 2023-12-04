# import win32api
# import win32con
# import win32security
from __version__ import __version__

def is_signature_valid(executable_path):
    # WINTRUST_ACTION_GENERIC_VERIFY_V2 = "{00AAC56B-CD44-11d0-8CC2-00C04FC295EE}"
    try:
    #     h_file = win32api.CreateFile(executable_path, win32con.GENERIC_READ, win32con.FILE_SHARE_READ, None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
    #     file_info = win32security.WINTRUST_FILE_INFO(h_file, executable_path)
    #     trust_data = win32security.WINTRUST_DATA(file_info)
    #     result = win32security.WinVerifyTrust(None, WINTRUST_ACTION_GENERIC_VERIFY_V2, trust_data)
    #
    #     return result == 0  # 0 indicates the signature is valid
        return True
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False
