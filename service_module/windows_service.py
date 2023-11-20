import win32service
import win32serviceutil
import win32event
import asyncio
import subprocess
import logging
import time
import psutil

from service_module.service_management import (
    get_service_name,
    get_agent_executable_path,
    load_configuration

)


class RewstService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'RewstAgentService'  # Placeholder, will be reset in __init__
    _svc_display_name_ = 'Rewst Agent Service'  # Placeholder, will be reset in __init__

    # Defining stop_event as a class variable
    stop_event = asyncio.Event()

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.process = None
        self.config_data = load_configuration(self.org_id)
        self.set_service_name(self.org_id)
        self.service_executable = get_agent_executable_path(self.org_id)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process_name = self.service_executable.replace('.exe', '')

    @classmethod
    def set_service_name(cls, org_id):
        cls._svc_name_ = get_service_name(org_id)
        cls._svc_display_name_ = f"Rewst Remote Service {org_id}"

    def report_running(self):
        try:
            # Start the service process
            self.process = subprocess.Popen([self.service_executable], shell=False)
            logging.info(f"Service started with PID {self.process.pid}")
            while not self.is_service_process_running():
                time.sleep(1)
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            time.sleep(5)
            if self.process.poll() is None:
                logging.info("Service is still running after 5 seconds.")
            else:
                logging.error("Service stopped unexpectedly.")
                self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        except Exception as e:
            logging.error(f"Exception in SvcDoRun: {e}")
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_service_process()
        while self.is_service_process_running():
            time.sleep(1)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def is_service_process_running(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == self.process_name:
                logging.info(f"Process {self.process_name} is running.")
                return True
            else:
                return False

    def stop_service_process(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == self.process_name:
                proc.terminate()
        return True

