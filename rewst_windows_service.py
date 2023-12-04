import logging
import os
import psutil
import servicemanager
import subprocess
import sys
import time
import win32serviceutil
import win32service
import win32event
from config_module.config_io import (
    get_org_id_from_executable_name,
    get_agent_executable_path
)
from service_module.verify_application_checksum import is_checksum_valid
from __version__ import __version__


class RewstWindowsService(win32serviceutil.ServiceFramework):

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
        self.process_ids = []

        self.org_id = get_org_id_from_executable_name(sys.argv)

        if self.org_id:
            logging.info(f"Found Org ID {self.org_id}")
            self.agent_executable_path = get_agent_executable_path(self.org_id)
        else:
            logging.warning(f"Did not find guid in executable name")
            return

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
                logging.info("Stop signal received.")
                break
            # Check if process is still running
            if self.process.poll() is not None:
                logging.warning("External process terminated unexpectedly. Restarting.")
                self.start_process()

    def start_process(self):
        try:
            if is_checksum_valid(self.agent_executable_path):
                logging.info(f"Verified that the executable {self.agent_executable_path} is valid signature.")
                process_name = os.path.basename(self.agent_executable_path).replace('.exe', '')
                logging.info(f"Launching process for {process_name}")
                self.process = subprocess.Popen(self.agent_executable_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                time.sleep(4)

                # Find and store PIDs of all processes with the matching name
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] == process_name:
                        self.process_ids.append(proc.info['pid'])
                        logging.info(f"Found process with PID {proc.info['pid']}.")
        except Exception as e:
            logging.exception(f"Failed to start external process: {e}")
            self.process_ids = []

    def stop_process(self):
        for pid in self.process_ids:
            try:
                logging.info(f"Attempting to terminate process with PID {pid}")
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=15)
                if proc.is_running():
                    logging.warning(f"Process with PID {pid} is still running. Attempting to kill.")
                    proc.kill()

                # Extra kill
                time.sleep(10)
                process_name = os.path.basename(self.agent_executable_path).replace('.exe', '')
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] == process_name:
                        logging.info(f"Killing process {proc.info['pid']}.")
                        proc.kill()
                        time.sleep(3)
            except psutil.NoSuchProcess:
                logging.info(f"Process with PID {pid} does not exist or has already terminated.")
            except Exception as e:
                logging.exception(f"Unable to terminate process ({e}).")
        self.process_ids = []
        logging.info("All processes stopped.")



def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Service is starting...")
    org_id = get_org_id_from_executable_name(sys.argv)

    if org_id:
        RewstWindowsService._svc_name_ = f"RewstRemoteAgent_{org_id}"
        RewstWindowsService._svc_display_name_ = f"Rewst Agent Service for Org {org_id}"
        logging.info(f"Found Org ID {org_id}")
    else:
        logging.warning("Org ID not found in executable name")

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RewstWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(RewstWindowsService)


if __name__ == '__main__':
    main()
