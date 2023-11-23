import asyncio
import threading
import win32serviceutil
import win32service
import win32event
import logging
from config_module.config_io import (
    load_configuration,
    get_org_id_from_executable_name
)
from iot_hub_module.connection_management import iot_hub_connection_loop


class RewstWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'RewstAgentService'
    _svc_display_name_ = 'Rewst Agent Service'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.reporter = None
        self.loop = None
        self.org_id = get_org_id_from_executable_name(sys.argv)
        self.config_data = load_configuration(self.org_id)

    def SvcDoRun(self):
        logging.info("Service is starting.")
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.start_async_loop()

    def start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Ensure that the async loop runs in a separate thread
        thread = threading.Thread(target=self.loop.run_until_complete, args=(iot_hub_connection_loop(self.config_data),))
        thread.start()
        thread.join()

    def SvcStop(self):
        logging.info("Service stop requested.")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(RewstWindowsService)


# Sets up event log handling
async def create_event_source(app_name):
    # Path to the registry key
    registry_key_path = f"SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{app_name}"
    # Registry key flags
    key_flags = win32con.KEY_SET_VALUE | win32con.KEY_CREATE_SUB_KEY

    # Ensure sys.executable is a string and contains the correct path
    assert isinstance(sys.executable, str), "sys.executable is not a string"
    event_message_file = sys.executable

    # Open or create the registry key
    with win32api.RegCreateKeyEx(win32con.HKEY_LOCAL_MACHINE, registry_key_path, 0, key_flags) as reg_key:
        try:
            logging.info(f"Logging for executable name: {event_message_file}")
            win32api.RegSetValueEx(reg_key, "EventMessageFile", 0, win32con.REG_SZ, event_message_file)

            types_supported = win32con.EVENTLOG_ERROR_TYPE | win32con.EVENTLOG_WARNING_TYPE | win32con.EVENTLOG_INFORMATION_TYPE
            logging.info(f"types_supported: {types_supported}")

            # Explicitly cast to int just to be sure
            win32api.RegSetValueEx(reg_key, "TypesSupported", 0, win32con.REG_DWORD, int(types_supported))
        except Exception as e:
            logging.error(f"Failed to set registry values: {e}")
