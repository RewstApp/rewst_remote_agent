import asyncio
import win32serviceutil
import win32service
import win32event
import servicemanager

from iot_hub_module.connection_management import iot_hub_connection_loop


class RewstWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'RewstAgentService'
    _svc_display_name_ = 'Rewst Agent Service'

    @classmethod
    def set_service_name(cls, org_id):
        cls._svc_name_ = f"RewstAgentService_{org_id}"
        cls._svc_display_name_ = f"Rewst Agent Service for {org_id}"

    def __init__(self, args, config_data):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.loop = asyncio.get_event_loop()
        self.is_running = True
        self.config_data = config_data
        self.stop_event = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)
        self.is_running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.stop_event = asyncio.Event()
        self.loop.run_until_complete(iot_hub_connection_loop(self.config_data, self.stop_event))


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(RewstWindowsService)

