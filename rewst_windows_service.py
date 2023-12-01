import asyncio
import logging
import servicemanager
import subprocess
import sys
import win32serviceutil
import win32service
import win32event
#import time
#import win32timezone
from config_module.config_io import (
    load_configuration,
    get_org_id_from_executable_name,
    get_agent_executable_path
)
# from argparse import ArgumentParser

from iot_hub_module.connection_management import iot_hub_connection_loop


class RewstWindowsService(win32serviceutil.ServiceFramework):
    #_svc_name_ = self.get_service_name()
    #_svc_display_name_ = 'Rewst Agent Service'

    #config_data = None

    # @classmethod
    # def parse_command_line(cls):
    #     win32serviceutil.HandleCommandLine(cls)

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
        _svc_name = self.get_service_name()
        _svc_display_name = self.get_service_display_name()

        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

        self.org_id = get_org_id_from_executable_name(sys.argv)

        if self.org_id:
            logging.info(f"Found Org ID {self.org_id}")
            self.agent_executable_path = get_agent_executable_path(self.org_id)
            self.config_data = load_configuration(self.org_id)
        else:
            logging.warning(f"Did not find guid in executable name")
            self.config_data = None
            return

        #self.setup_logging()


    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_process()
        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)


    def SvcDoRun(self):
        logging.info(f"Starting SvcDoRun for {self._svc_name_}")
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.start_process()
        while True:
            # Check if stop signal received
            if win32event.WaitForSingleObject(self.hWaitStop, 5000) == win32event.WAIT_OBJECT_0:
                break
            # Check if process is still running
            if self.process.poll() is not None:
                logging.warning("External process terminated unexpectedly.")
                break

    def start_process(self):
        try:
            self.process = subprocess.Popen((self.agent_executable_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logging.info("External process started.")
        except Exception as e:
            logging.exception(f"Failed to start external process: {e}")
            self.process = None

    def stop_process(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                logging.exception(f"Unable to terminate process ({e}), attempting to kill().")
                self.process.kill()
                self.process.wait()

            self.process = None
            logging.info("External process stopped.")


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Service is starting...")
    org_id = get_org_id_from_executable_name(sys.argv)

    if org_id:
        RewstWindowsService._svc_name_ = f"RewstRemoteAgent_{org_id}"
        RewstWindowsService._svc_display_name_ = f"Rewst Agent Service for Org {org_id}"
        logging.info(f"Found Org ID {org_id}")
        config_data = load_configuration(org_id)
    else:
        logging.warning("Org ID not found in executable name")
        config_data = None

    if config_data is None:
        logging.error("No configuration found. Exiting.")
        return

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RewstWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(RewstWindowsService)


if __name__ == '__main__':
    main()
