""" Module for defining the remote agent windows service """

import asyncio
from typing import List

import logging
import sys

import servicemanager
import win32serviceutil
import win32service

import rewst_remote_agent

from config_module.config_io import (
    get_org_id_from_executable_name,
    get_agent_executable_path
)
from __version__ import __version__


class RewstWindowsService(win32serviceutil.ServiceFramework):
    """
    Rewst windows service class implementation
    """

    @classmethod
    def set_service_name(cls, org_id: str) -> None:
        """
        Set the service name using the organization ID.

        Args:
            org_id (str): Organization identifier in Rewst platform.
        """
        cls._svc_name_ = f"RewstRemoteAgent_{org_id}"
        cls._svc_display_name_ = f"Rewst Agent Service for Org {org_id}"

    @classmethod
    def get_service_name(cls) -> str:
        """
        Get the service name.

        Returns:
            str: Service name.
        """
        return cls._svc_name_

    @classmethod
    def get_service_display_name(cls) -> str:
        """
        Get the service display name.

        Returns:
            str: Service display name.
        """
        return cls._svc_display_name_

    def __init__(self, args: List[str]):
        """
        Rewst windows service class constructor.

        Args:
            args (_type_): _description_
        """
        _svc_name = self.get_service_name()
        _svc_display_name = self.get_service_display_name()

        win32serviceutil.ServiceFramework.__init__(self, args)

        self.org_id = get_org_id_from_executable_name(sys.argv)

        if self.org_id:
            logging.info("Found Org ID %s", self.org_id)
            self.agent_executable_path = get_agent_executable_path(self.org_id)
        else:
            logging.warning("Did not find guid in executable name")

    def SvcStop(self) -> None:  # pylint: disable=invalid-name
        """
        Handler when the service is stopped by the OS.
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        rewst_remote_agent.stop_event.set()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self) -> None:  # pylint: disable=invalid-name
        """
        Handler when the service ss performing work in the system.
        """
        logging.info("Starting SvcDoRun for %s", self._svc_name_)
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        # Do not use signal handlers since this will be ran in windows
        asyncio.run(rewst_remote_agent.main(False))


def main() -> None:
    """
    Main entry point of the program.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Service is starting...")
    org_id = get_org_id_from_executable_name(sys.argv)

    if org_id:
        RewstWindowsService.set_service_name(org_id)
        logging.info("Found Org ID %s", org_id)
    else:
        logging.warning("Org ID not found in executable name")

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RewstWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(RewstWindowsService)


if __name__ == "__main__":
    main()
