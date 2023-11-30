import asyncio
import logging
import servicemanager
import sys
import win32serviceutil
import win32service
import win32event
import win32timezone
from config_module.config_io import (
    load_configuration,
    setup_file_logging,
    get_org_id_from_executable_name
)

from iot_hub_module.connection_management import iot_hub_connection_loop


class RewstWindowsService(win32serviceutil.ServiceFramework):
    #_svc_name_ = self.get_service_name()
    #_svc_display_name_ = 'Rewst Agent Service'

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
        self.setup_logging()

        self.org_id = get_org_id_from_executable_name(sys.argv)

        if self.org_id:
            logging.info(f"Found Org ID {self.org_id}")
            self.config_data = load_configuration(self.org_id)
        else:
            logging.warning(f"Did not find guid in executable name")
            self.config_data = None


    def setup_logging(self):
        setup_file_logging(self.config_data['org_id'])

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop()
        if self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)
        self.is_running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.start()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        logging.info(f"Running As a Service named {self._svc_name_}")
        #servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))
        self.stop_event = asyncio.Event()
        self.loop.run_until_complete(iot_hub_connection_loop(self.config_data, self.stop_event))
        ##asyncio.ensure_future(iot_hub_connection_loop(self.config_data, self.stop_event))
        ##self.loop.run_forever()


        # while True:
        #     import time
        #     logging.info("Service is running in test mode.")
        #     time.sleep(10)  # Sleep for 10 seconds
        #
        #     # Check if a stop request has been made
        #     if self.stop_event.is_set():
        #         logging.info("Service stop requested. Exiting test loop.")
        #         break

    def start(self):
        pass

    def stop(self):
        pass


if __name__ == '__main__':
    org_id = get_org_id_from_executable_name(sys.argv)

    if org_id:
        RewstWindowsService._svc_name_ = f"RewstRemoteAgent_{org_id}"
        RewstWindowsService._svc_display_name_ = f"Rewst Agent Service for Org {org_id}"

    win32serviceutil.HandleCommandLine(RewstWindowsService)


