import asyncio
import logging
from logging.handlers import RotatingFileHandler
import os
import win32serviceutil
import win32service
import win32event
#import servicemanager
from config_module.config_io import get_logging_path

from iot_hub_module.connection_management import iot_hub_connection_loop


class RewstWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'RewstRemoteAgent'
    _svc_display_name_ = 'Rewst Agent Service'

    config_data = None

    @classmethod
    def set_service_name(cls, org_id):
        cls._svc_name_ = f"RewstRemoteAgent_{org_id}"
        cls._svc_display_name_ = f"Rewst Agent Service for Org {org_id}"

    @classmethod
    def get_service_name(cls):
        return cls._svc_name_


    @classmethod
    def get_service_display_name(cls):
        return cls._svc_display_name_

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.loop = asyncio.get_event_loop()
        self.is_running = True
        self.config_data = RewstWindowsService.config_data
        self.stop_event = None

    def setup_logging(self):
        log_file_path = get_logging_path(self.config_data['org_id'])
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            handlers=[RotatingFileHandler(log_file_path, maxBytes=10485760, backupCount=3)])
        logging.info("Logging initialized.")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)
        self.is_running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        logging.info(f"Running As a Service named {self._svc_name_}")
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        #servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))
        self.stop_event = asyncio.Event()
        self.loop.run_until_complete(iot_hub_connection_loop(self.config_data, self.stop_event))


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(RewstWindowsService)
    self.setup_logging()
