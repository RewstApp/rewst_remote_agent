import logging
import logging.handlers
import platform

# Determine the operating system
os_type = platform.system().lower()

# Configure logging
if os_type == 'windows':
    # Log to Windows Event Log on Windows systems
    nt_event_log_handler = logging.handlers.NTEventLogHandler('RewstService')
    logging.basicConfig(
        level=logging.INFO,
        handlers=[nt_event_log_handler]
    )
else:
    # Log to console on non-Windows systems
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

class ConnectionError(Exception):
    """Raised when there's a problem connecting to the IoT Hub."""
    pass

class ConfigurationError(Exception):
    """Raised when there's a problem with configuration data."""
    pass

class ServiceError(Exception):
    """Raised when there's a problem with the service management."""
    pass

def handle_exception(e):
    """Log the exception and take any necessary action."""
    logging.error(f"An error occurred: {e}")
    # Additional error handling logic can go here

def create_event_source(app_name):
    """Create an event source for logging to the Windows Event Log."""
    if os_type != 'windows':
        return  # Exit if not on a Windows system
    
    import win32api
    import win32con

    registry_key = f"SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{app_name}"
    key_flags = win32con.KEY_SET_VALUE | win32con.KEY_CREATE_SUB_KEY
    try:
        # Try to open the registry key
        reg_key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, registry_key, 0, key_flags)
    except Exception as e:
        logging.error(f"Failed to open or create registry key: {e}")
        return

    try:
        # Set the EventMessageFile registry value
        event_message_file = win32api.GetModuleHandle(None)
        win32api.RegSetValueEx(reg_key, "EventMessageFile", 0, win32con.REG_SZ, event_message_file)
        win32api.RegSetValueEx(reg_key, "TypesSupported", 0, win32con.REG_DWORD, win32con.EVENTLOG_ERROR_TYPE | win32con.EVENTLOG_WARNING_TYPE | win32con.EVENTLOG_INFORMATION_TYPE)
    except Exception as e:
        logging.error(f"Failed to set registry values: {e}")
    finally:
        win32api.RegCloseKey(reg_key)

# Create an event source for logging to the Windows Event Log
if os_type == 'windows':
    create_event_source('RewstService')
