import asyncio
import win32service
import win32serviceutil
import win32event
import logging
import sys
import threading
import time
import win32con
import win32api
from service_module.service_management import (
    get_service_name,
    get_agent_executable_path
)
from config_module.config_io import (
    load_configuration,
    get_org_id_from_executable_name
)
from iot_hub_module.connection_management import (
    iot_hub_connection_loop,
    ConnectionManager
)


class RewstWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'RewstAgentService'  # Placeholder, will be reset in __init__
    _svc_display_name_ = 'Rewst Agent Service'  # Placeholder, will be reset in __init__

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.org_id = None
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.config_data = None
        self.service_executable = None
        self.process_name = None
        self.is_running = True

    def set_up(self, org_id):
        self.config_data = load_configuration(org_id)
        self.set_service_name(org_id)
        self.service_executable = get_agent_executable_path(org_id)
        self.process_name = self.service_executable.replace('.exe', '')

    @classmethod
    def set_service_name(cls, org_id):
        cls._svc_name_ = get_service_name(org_id)
        cls._svc_display_name_ = f"Rewst Remote Service {org_id}"

    def SvcDoRun(self):
        logging.info("Service is starting.")

        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        # Set up the event loop for the new thread
        self.loop = asyncio.new_event_loop()
        asyncio_thread = threading.Thread(target=self.asyncio_thread)
        asyncio_thread.start()

        # Wait for the stop signal
        while self.is_running:
            # You can fine-tune this time
            time.sleep(1)

        # Clean up: Join the asyncio thread
        self.loop.call_soon_threadsafe(self.loop.stop)
        asyncio_thread.join()

        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def asyncio_thread(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(iot_hub_connection_loop(config_data=self.config_data))
        self.loop.close()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_running = False  # Signal the service to stop
        ConnectionManager.disconnect(self)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def is_service_process_running(self):
        if self.ReportServiceStatus.is_running():
            return True
        return False

    def stop_service_process(self):
        self.SvcStop()
        return True


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
