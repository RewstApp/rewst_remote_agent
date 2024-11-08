"""
Tests for service management module
"""

from unittest.mock import patch, MagicMock
import unittest
import pywintypes

from service_module.service_management import (
    get_service_name,
    is_service_installed,
    is_service_running,
    restart_service,
    stop_service,
)


class TestServiceManagement(unittest.TestCase):
    """
    Unit test class for service management module
    """

    @patch("service_module.service_management.os_type", "windows")
    @patch("rewst_windows_service.RewstWindowsService.get_service_name")
    def test_get_service_name_windows(self, mock_get_service_name: MagicMock) -> None:
        """
        Test the get_service_name() function for Windows platform.

        Args:
            mock_get_service_name (MagicMock): Mock instance to get the service name.
        """
        mock_get_service_name.return_value = "TestServiceName"
        service_name = get_service_name("123")
        self.assertEqual(service_name, "TestServiceName")
        mock_get_service_name.assert_called_once()

    @patch("service_module.service_management.os_type", "linux")
    def test_get_service_name_linux(self) -> None:
        """
        Test the get_service_name() function for Linux platform.
        """
        service_name = get_service_name("123")
        self.assertEqual(service_name, "RewstRemoteAgent_123")

    @patch("service_module.service_management.os_type", "windows")
    @patch(
        "rewst_windows_service.RewstWindowsService.get_service_name",
        return_value="RewstRemoteAgent_123",
    )
    @patch("win32serviceutil.QueryServiceStatus", return_value=True)
    def test_is_service_installed_windows_installed(
        self,
        mock_query_service_status: MagicMock,
        mock_get_service_name: MagicMock,
    ) -> None:
        """
        Test the is_service_installed() function for Windows platform given that the service is installed.

        Args:
            mock_query_service_status (MagicMock): Mock instance for QueryServiceStatus() function.
            mock_get_service_name (MagicMock): Mock instance for RewstWindowsService.get_service_name() method.
        """
        with self.assertLogs(level="INFO"):
            result = is_service_installed("123")

        self.assertTrue(result)
        mock_query_service_status.assert_called_once()
        mock_get_service_name.assert_called_once()

    @patch("service_module.service_management.os_type", "windows")
    @patch(
        "rewst_windows_service.RewstWindowsService.get_service_name",
        return_value="RewstRemoteAgent_1234",
    )
    @patch(
        "win32serviceutil.QueryServiceStatus",
        side_effect=Exception,
    )
    def test_is_service_installed_windows_not_installed(
        self, mock_query_service_status: MagicMock, mock_get_service_name: MagicMock
    ) -> None:
        """
        Test the is_service_installed() function for Windows platform given that the service is not installed.

        Args:
            mock_query_service_status (MagicMock): Mock instance for QueryServiceStatus() function.
            mock_get_service_name (MagicMock): Mock instance for RewstWindowsService.get_service_name() method.
        """
        with self.assertLogs(level="ERROR"):
            result = is_service_installed("123")

        self.assertFalse(result)
        mock_query_service_status.assert_called_once()
        mock_get_service_name.assert_called_once()

    @patch("service_module.service_management.os_type", "linux")
    @patch("os.path.exists", return_value=True)
    def test_is_service_installed_linux_installed(self, mock_exists: MagicMock) -> None:
        """
        Test the is_service_installed() function for Linux platform given the service is installed.

        Args:
            mock_exists (MagicMock): Mock instance for exists().
        """

        with self.assertLogs(level="INFO"):
            result = is_service_installed("123")
        self.assertTrue(result)
        mock_exists.assert_called_once_with(
            "/etc/systemd/system/RewstRemoteAgent_123.service"
        )

    @patch("psutil.process_iter", return_value=[MagicMock(info={"name": "agent"})])
    @patch(
        "service_module.service_management.get_agent_executable_path",
        return_value="/path/to/agent",
    )
    def test_is_service_running(
        self, mock_get_agent_executable_path: MagicMock, mock_process_iter: MagicMock
    ) -> None:
        """
        Test is_service_running() function given the service is running.

        Args:
            mock_get_agent_executable_path (MagicMock): Mock instance for get_agent_executable_path().
            mock_process_iter (MagicMock): Mock instance for process_iter().
        """
        result = is_service_running("123")
        self.assertEqual(result, "agent")
        mock_get_agent_executable_path.assert_called_once_with("123")
        mock_process_iter.assert_called_once()

    @patch(
        "psutil.process_iter", return_value=[MagicMock(info={"name": "other_process"})]
    )
    @patch(
        "service_module.service_management.get_agent_executable_path",
        return_value="/path/to/agent",
    )
    def test_is_service_running_not_running(
        self, mock_get_agent_executable_path: MagicMock, mock_process_iter: MagicMock
    ) -> None:
        """
        Test is_service_running() function given the service is not running.

        Args:
            mock_get_agent_executable_path (MagicMock): Mock instance for get_agent_executable_path().
            mock_process_iter (MagicMock): Mock instance for process_iter().
        """
        result = is_service_running("123")
        self.assertFalse(result)
        mock_get_agent_executable_path.assert_called_once()
        mock_process_iter.assert_called_once()

    @patch("service_module.service_management.stop_service")
    @patch("service_module.service_management.start_service")
    def test_restart_service(self, mock_start: MagicMock, mock_stop: MagicMock) -> None:
        """
        Test the restart_service().

        Args:
            mock_start (MagicMock): Mock object for start_service().
            mock_stop (MagicMock): Mock object for stop_service().
        """
        org_id = "rewst-staff"
        restart_service(org_id)
        mock_start.assert_called_once_with(org_id)
        mock_stop.assert_called_once_with(org_id)


ORG_ID = "rewst-staff"
SERVICE_NAME = "rewst-service"


@patch("service_module.service_management.os_type", "windows")
class TestServiceManagementWindows(unittest.TestCase):
    """
    Test service_management module on Windows platform.
    """

    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("win32serviceutil.QueryServiceStatus", return_value=True)
    @patch("win32serviceutil.StopService")
    def test_stop_service(
        self,
        mock_stop: MagicMock,
        mock_query_service_status: MagicMock,
        mock_get_service_name: MagicMock,
    ) -> None:
        """
        Test stop_service().

        Args:
            mock_stop (MagicMock): Mock object for win32serviceutil.StopService().
            mock_query_service_status (MagicMock): Mock object for win32serviceutil.QueryServiceStatus().
            mock_get_service_name (MagicMock): Mock object for get_service_name().
        """
        stop_service(ORG_ID)

        mock_stop.assert_called_once_with(SERVICE_NAME)
        mock_query_service_status.assert_called_once_with(SERVICE_NAME)
        mock_get_service_name.assert_called_once_with(ORG_ID)

    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("win32serviceutil.QueryServiceStatus", return_value=True)
    @patch("win32serviceutil.StopService", side_effect=pywintypes.error)
    def test_stop_service_failed(
        self,
        mock_stop: MagicMock,
        mock_query_service_status: MagicMock,
        mock_get_service_name: MagicMock,
    ) -> None:
        """
        Test stop_service() given it failed.

        Args:
            mock_stop (MagicMock): Mock object for win32serviceutil.StopService().
            mock_query_service_status (MagicMock): Mock object for win32serviceutil.QueryServiceStatus().
            mock_get_service_name (MagicMock): Mock object for get_service_name().
        """
        with self.assertLogs(level="ERROR"):
            stop_service(ORG_ID)

        mock_stop.assert_called_once_with(SERVICE_NAME)
        mock_query_service_status.assert_called_once_with(SERVICE_NAME)
        mock_get_service_name.assert_called_once_with(ORG_ID)


if __name__ == "__main__":
    unittest.main()
