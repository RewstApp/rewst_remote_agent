"""
Tests for service management module
"""

from unittest.mock import patch, MagicMock
import unittest
import subprocess
import pywintypes

from service_module.service_management import (
    get_service_name,
    is_service_installed,
    is_service_running,
    restart_service,
    stop_service,
    start_service,
    check_service_status,
)

ORG_ID = "rewst-staff"
SERVICE_NAME = "rewst-service"


class TestServiceManagement(unittest.TestCase):
    """
    Unit test class for service management module
    """

    @patch("psutil.process_iter", return_value=[MagicMock(info={"name": "agent"})])
    @patch(
        "service_module.service_management.get_agent_executable_path",
        return_value="/path/to/agent",
    )
    def test_is_service_running_given_running(
        self, mock_get_agent_executable_path: MagicMock, mock_process_iter: MagicMock
    ) -> None:
        """
        Test is_service_running() given the service is running.

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
    def test_is_service_running_given_not_running(
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
        restart_service(ORG_ID)
        mock_start.assert_called_once_with(ORG_ID)
        mock_stop.assert_called_once_with(ORG_ID)

    @patch("builtins.print")
    @patch("service_module.service_management.get_service_name")
    @patch("service_module.service_management.os_type", "nil")
    def test_check_service_status_given_unsupported(
        self, mock_get_service_name: MagicMock, mock_print: MagicMock
    ):
        """
        Test check_service_status() given unsupported os.

        Args:
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
        """        
        check_service_status(ORG_ID)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Unsupported OS type: nil")


@patch("service_module.service_management.os_type", "windows")
class TestServiceManagementWindows(unittest.TestCase):
    """
    Test service_management on Windows platform.
    """

    @patch(
        "rewst_windows_service.RewstWindowsService.get_service_name",
        return_value="TestServiceName",
    )
    def test_get_service_name(self, mock_get_service_name: MagicMock) -> None:
        """
        Test the get_service_name().

        Args:
            mock_get_service_name (MagicMock): Mock instance to get the service name.
        """
        service_name = get_service_name("123")
        self.assertEqual(service_name, "TestServiceName")
        mock_get_service_name.assert_called_once()

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

    # pylint: disable=E1101
    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("win32serviceutil.QueryServiceStatus", return_value=True)
    @patch("win32serviceutil.StopService", side_effect=pywintypes.error)
    def test_stop_service_given_failed(
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

    @patch(
        "rewst_windows_service.RewstWindowsService.get_service_name",
        return_value="RewstRemoteAgent_123",
    )
    @patch("win32serviceutil.QueryServiceStatus", return_value=True)
    def test_is_service_installed_given_installed(
        self,
        mock_query_service_status: MagicMock,
        mock_get_service_name: MagicMock,
    ) -> None:
        """
        Test the is_service_installed() function given that the service is installed.

        Args:
            mock_query_service_status (MagicMock): Mock instance for QueryServiceStatus() function.
            mock_get_service_name (MagicMock): Mock instance for RewstWindowsService.get_service_name() method.
        """
        with self.assertLogs(level="INFO"):
            result = is_service_installed("123")

        self.assertTrue(result)
        mock_query_service_status.assert_called_once()
        mock_get_service_name.assert_called_once()

    @patch(
        "rewst_windows_service.RewstWindowsService.get_service_name",
        return_value="RewstRemoteAgent_1234",
    )
    @patch(
        "win32serviceutil.QueryServiceStatus",
        side_effect=Exception,
    )
    def test_is_service_installed_given_not_installed(
        self, mock_query_service_status: MagicMock, mock_get_service_name: MagicMock
    ) -> None:
        """
        Test the is_service_installed() function given that the service is not installed.

        Args:
            mock_query_service_status (MagicMock): Mock instance for QueryServiceStatus() function.
            mock_get_service_name (MagicMock): Mock instance for RewstWindowsService.get_service_name() method.
        """
        with self.assertLogs(level="ERROR"):
            result = is_service_installed("123")

        self.assertFalse(result)
        mock_query_service_status.assert_called_once()
        mock_get_service_name.assert_called_once()

    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("win32serviceutil.StartService")
    def test_start_service(
        self, mock_start_service: MagicMock, mock_get_service_name: MagicMock
    ) -> None:
        """
        Test start_service().

        Args:
            mock_start_service (MagicMock): Mock instance for win32serviceutil.StartService().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
        """
        with self.assertLogs(level="INFO"):
            start_service(ORG_ID)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_start_service.assert_called_once_with(SERVICE_NAME)

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch("subprocess.run")
    def test_check_service_status(
        self,
        mock_run: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status().

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        # Setup the return value of subproces.run()
        mock_run.return_value = MagicMock()
        mock_run.return_value.stdout.strip.return_value = "Ok"

        check_service_status(ORG_ID)
        mock_run.assert_called_once()
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Service status: Ok")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch("win32serviceutil.QueryServiceStatus", return_value=[0, "Ok"])
    def test_check_service_status(
        self,
        mock_query: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status().

        Args:
            mock_query (MagicMock): Mock instance for win32serviceutil.QueryServiceStatus().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        check_service_status(ORG_ID)
        mock_query.assert_called_once_with(SERVICE_NAME)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Service status: Ok")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch("win32serviceutil.QueryServiceStatus", side_effect=Exception("Failed"))
    def test_check_service_status_given_failed(
        self,
        mock_query: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status() given it failed.

        Args:
            mock_query (MagicMock): Mock instance for win32serviceutil.QueryServiceStatus().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        check_service_status(ORG_ID)
        mock_query.assert_called_once_with(SERVICE_NAME)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Error: Failed")


@patch("service_module.service_management.os_type", "linux")
class TestServiceManagementLinux(unittest.TestCase):
    """
    Test service_management on Linux platform.
    """

    def test_get_service_name(self) -> None:
        """
        Test get_service_name().
        """
        service_name = get_service_name(SERVICE_NAME)
        self.assertEqual(service_name, f"RewstRemoteAgent_{SERVICE_NAME}")

    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("subprocess.run")
    def test_stop_service(
        self, mock_run: MagicMock, mock_get_service_name: MagicMock
    ) -> None:
        """
        Test stop_service().

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
        """
        stop_service(ORG_ID)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_run.assert_called_once_with(f"systemctl stop {SERVICE_NAME}")

    @patch("os.path.exists", return_value=True)
    def test_is_service_installed_given_installed(self, mock_exists: MagicMock) -> None:
        """
        Test is_service_installed() given the service is installed.

        Args:
            mock_exists (MagicMock): Mock instance for exists().
        """

        with self.assertLogs(level="INFO"):
            result = is_service_installed(SERVICE_NAME)
        self.assertTrue(result)
        mock_exists.assert_called_once_with(
            f"/etc/systemd/system/RewstRemoteAgent_{SERVICE_NAME}.service"
        )

    @patch("os.path.exists", return_value=False)
    def test_is_service_installed_given_not_installed(
        self, mock_exists: MagicMock
    ) -> None:
        """
        Test is_service_installed() given the service is not installed.

        Args:
            mock_exists (MagicMock): Mock instance for exists().
        """

        with self.assertLogs(level="INFO"):
            result = is_service_installed(SERVICE_NAME)
        self.assertFalse(result)
        mock_exists.assert_called_once_with(
            f"/etc/systemd/system/RewstRemoteAgent_{SERVICE_NAME}.service"
        )

    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("subprocess.run")
    def test_start_service(
        self, mock_run: MagicMock, mock_get_service_name: MagicMock
    ) -> None:
        """
        Test start_service().

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
        """
        with self.assertLogs(level="INFO"):
            start_service(ORG_ID)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_run.assert_called_once_with(f"systemctl start {SERVICE_NAME}")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch("subprocess.run")
    def test_check_service_status(
        self,
        mock_run: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status().

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        # Setup the return value of subproces.run()
        mock_run.return_value = MagicMock()
        mock_run.return_value.stdout.strip.return_value = "Ok"

        check_service_status(ORG_ID)
        mock_run.assert_called_once()
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Service status: Ok")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(returncode=1, cmd=1, output="Failed"),
    )
    def test_check_service_status_given_called_process_error(
        self,
        mock_run: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status() given the subprocess.CalledProcessError() is raised.

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        check_service_status(ORG_ID)
        mock_run.assert_called_once()
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Error: Failed")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch("subprocess.run", side_effect=Exception("Failed"))
    def test_check_service_status_given_exception(
        self,
        mock_run: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status() given the Exception() is raised.

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        check_service_status(ORG_ID)
        mock_run.assert_called_once()
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Error: Failed")


@patch("service_module.service_management.os_type", "darwin")
class TestServiceManagementDarwin(unittest.TestCase):
    """
    Test service_management on Darwin platform.
    """

    def test_get_service_name(self) -> None:
        """
        Test get_service_name().
        """
        service_name = get_service_name(SERVICE_NAME)
        self.assertEqual(service_name, f"RewstRemoteAgent_{SERVICE_NAME}")

    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("subprocess.run")
    def test_stop_service(
        self, mock_run: MagicMock, mock_get_service_name: MagicMock
    ) -> None:
        """
        Test stop_service().

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
        """
        stop_service(ORG_ID)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_run.assert_called_once_with(f"launchctl stop {SERVICE_NAME}")

    @patch("os.path.expanduser", new=lambda path: path)
    @patch("os.path.exists", return_value=True)
    def test_is_service_installed(self, mock_exists: MagicMock) -> None:
        """
        Test is_service_installed() given the service is installed.

        Args:
            mock_exists (MagicMock): Mock instance for os.path.exists().
            mock_expanduser (MagicMock): Mock instance for os.path.expanduser().
        """
        with self.assertLogs(level="INFO"):
            result = is_service_installed(ORG_ID)
            self.assertTrue(result)

        mock_exists.assert_called_once_with(
            f"~/Library/LaunchAgents/RewstRemoteAgent_{ORG_ID}.plist"
        )

    @patch(
        "service_module.service_management.get_service_name",
        return_value=SERVICE_NAME,
    )
    @patch("subprocess.run")
    def test_start_service(
        self, mock_run: MagicMock, mock_get_service_name: MagicMock
    ) -> None:
        """
        Test start_service().

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
        """
        with self.assertLogs(level="INFO"):
            start_service(ORG_ID)
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_run.assert_called_once_with(f"launchctl start {SERVICE_NAME}")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch("subprocess.run")
    def test_check_service_status(
        self,
        mock_run: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status().

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        test_cases = ((SERVICE_NAME, "Running"), ("", "Not Running"))

        for stdout, message in test_cases:
            with self.subTest(stdout=stdout, message=message):
                # Setup the return value of subproces.run()
                mock_run.return_value = MagicMock(stdout=stdout)

                check_service_status(ORG_ID)
                mock_run.assert_called()
                mock_get_service_name.assert_called_with(ORG_ID)
                mock_print.assert_called_with(f"Service status: {message}")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(returncode=1, cmd=1, output="Failed"),
    )
    def test_check_service_status_given_called_process_error(
        self,
        mock_run: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status() given the subprocess.CalledProcessError() is raised.

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        check_service_status(ORG_ID)
        mock_run.assert_called_once()
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Error: Failed")

    @patch("builtins.print")
    @patch(
        "service_module.service_management.get_service_name", return_value=SERVICE_NAME
    )
    @patch("subprocess.run", side_effect=Exception("Failed"))
    def test_check_service_status_given_exception(
        self,
        mock_run: MagicMock,
        mock_get_service_name: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        """
        Test check_service_status() given the Exception() is raised.

        Args:
            mock_run (MagicMock): Mock instance for subprocess.run().
            mock_get_service_name (MagicMock): Mock instance for get_service_name().
            mock_print (MagicMock): Mock instance for print().
        """
        check_service_status(ORG_ID)
        mock_run.assert_called_once()
        mock_get_service_name.assert_called_once_with(ORG_ID)
        mock_print.assert_called_once_with("Error: Failed")


if __name__ == "__main__":
    unittest.main()
