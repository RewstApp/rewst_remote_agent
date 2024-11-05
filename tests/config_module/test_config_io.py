""" Test module for config_module.config_io """

import os
from uuid import uuid4
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock
from config_module.config_io import (
    get_executable_folder,
    get_service_manager_path,
    get_agent_executable_path,
    get_service_executable_path,
    get_logging_path,
    get_config_file_path,
    save_configuration,
    load_configuration,
    get_org_id_from_executable_name,
    setup_file_logging,
)


# Mock organization ID for tests
ORG_ID = str(uuid4())


class TestConfigIO(unittest.TestCase):
    """Test class for config_module.config_io"""

    @patch("platform.system", return_value="Windows")
    @patch.dict(os.environ, {"ProgramFiles": "C:\\Program Files"})
    def test_get_executable_folder_windows(self, mock_system: MagicMock) -> None:
        """Test the get_executable_folder() function for Windows platform

        Args:
            mock_system (MagicMock): Mock instance for platform.system()
        """

        path = get_executable_folder(ORG_ID)
        mock_system.assert_called()
        self.assertEqual(path, f"C:\\Program Files\\RewstRemoteAgent\\{ORG_ID}\\")

    @patch("platform.system", return_value="Linux")
    def test_get_executable_folder_linux(self, mock_system: MagicMock) -> None:
        """Test the get_executable_folder() function for Linux platform

        Args:
            mock_system (MagicMock): Mock instance for platform.system()
        """

        path = get_executable_folder(ORG_ID)
        mock_system.assert_called()
        self.assertEqual(path, "/usr/local/bin/")

    @patch("platform.system", return_value="Darwin")
    def test_get_executable_folder_darwin(self, mock_system: MagicMock) -> None:
        """Test the get_executable_folder() function for Darwin platform

        Args:
            mock_system (MagicMock): Mock instance for platform.system()
        """

        path = get_executable_folder(ORG_ID)
        mock_system.assert_called()
        expected_path = os.path.expanduser(
            f"~/Library/Application Support/RewstRemoteAgent/{ORG_ID}/"
        )
        self.assertEqual(path, expected_path)

    @patch("platform.system", return_value="Unsupported")
    @patch("logging.error")
    def test_get_executable_folder_unsupported(
        self, mock_system: MagicMock, mock_error: MagicMock
    ) -> None:
        """Test the get_executable_folder() function for Unsupported platform

        Args:
            mock_system (MagicMock): Mock instance for get_executable_folder()
            mock_error (MagicMock): Mock instance for logging.error()
        """

        with self.assertRaises(SystemExit):
            get_executable_folder(ORG_ID)

        mock_error.assert_called()
        mock_system.assert_called()

    @patch("config_module.config_io.os_type", "windows")
    @patch(
        "config_module.config_io.get_executable_folder",
        return_value=f"C:\\Program Files\\RewstRemoteAgent\\{ORG_ID}\\",
    )
    def test_get_service_manager_path_windows(
        self, mock_get_executable_folder: MagicMock
    ) -> None:
        """Test the get_service_manager_path() function for Windows platform

        Args:
            mock_get_executable_folder (MagicMock): Mock instance for get_executable_folder()
        """

        path = get_service_manager_path(ORG_ID)
        mock_get_executable_folder.assert_called()
        self.assertEqual(
            path,
            f"C:\\Program Files\\RewstRemoteAgent\\{ORG_ID}\\"
            + f"rewst_service_manager.win_{ORG_ID}.exe",
        )

    @patch("config_module.config_io.os_type", "linux")
    @patch(
        "config_module.config_io.get_executable_folder", return_value="/usr/local/bin/"
    )
    def test_get_service_manager_path_linux(
        self, mock_get_executable_folder: MagicMock
    ) -> None:
        """Test the get_service_manager_path() function for Linux platform

        Args:
            mock_get_executable_folder (MagicMock): Mock instance for get_executable_folder()
        """

        path = get_service_manager_path(ORG_ID)
        mock_get_executable_folder.assert_called()
        self.assertEqual(
            path,
            f"/usr/local/bin/rewst_service_manager.linux_{ORG_ID}.bin",
        )

    @patch("config_module.config_io.os_type", "darwin")
    @patch(
        "config_module.config_io.get_executable_folder", return_value="/usr/local/bin/"
    )
    def test_get_service_manager_path_darwin(
        self, mock_get_executable_folder: MagicMock
    ) -> None:
        """Test the get_service_manager_path() function for Darwin platform

        Args:
            mock_get_executable_folder (MagicMock): Mock instance for get_executable_folder()
        """

        path = get_service_manager_path(ORG_ID)
        mock_get_executable_folder.assert_called()
        self.assertEqual(
            path,
            f"/usr/local/bin/rewst_service_manager.macos_{ORG_ID}.bin",
        )

    @patch("config_module.config_io.os_type", "unsupported")
    @patch("logging.error")
    def test_get_service_manager_path_unsupported(self, mock_error: MagicMock) -> None:
        """Test the get_service_manager_path() function for Unsupported platform

        Args:
            mock_error (MagicMock): Mock instance for logging.error()
        """

        with self.assertRaises(SystemExit):
            get_service_manager_path(ORG_ID)
        mock_error.assert_called()

    @patch("config_module.config_io.os_type", "windows")
    @patch(
        "config_module.config_io.get_executable_folder",
        return_value=f"C:\\Program Files\\RewstRemoteAgent\\{ORG_ID}\\",
    )
    def test_get_agent_executable_path_windows(
        self, mock_get_executable_folder: MagicMock
    ) -> None:
        """Test the get_agent_executable_path() function for Windows platform

        Args:
            mock_get_executable_folder (MagicMock): Mock instance for get_executable_folder()
        """

        path = get_agent_executable_path(ORG_ID)
        mock_get_executable_folder.assert_called()
        self.assertEqual(
            path,
            f"C:\\Program Files\\RewstRemoteAgent\\{ORG_ID}\\rewst_remote_agent_{ORG_ID}.win.exe",
        )

    @patch("config_module.config_io.os_type", "linux")
    @patch(
        "config_module.config_io.get_executable_folder", return_value="/usr/local/bin/"
    )
    def test_get_agent_executable_path_linux(
        self, mock_get_executable_folder: MagicMock
    ) -> None:
        """Test the get_agent_executable_path() function for Linux platform

        Args:
            mock_get_executable_folder (MagicMock): Mock instance for get_executable_folder()
        """

        path = get_agent_executable_path(ORG_ID)
        mock_get_executable_folder.assert_called()
        self.assertEqual(path, f"/usr/local/bin/rewst_remote_agent_{ORG_ID}.linux.bin")

    @patch("config_module.config_io.os_type", "darwin")
    @patch(
        "config_module.config_io.get_executable_folder", return_value="/usr/local/bin/"
    )
    def test_get_agent_executable_path_darwin(
        self, mock_get_executable_folder: MagicMock
    ) -> None:
        """Test the get_agent_executable_path() function for Darwin platform

        Args:
            mock_get_executable_folder (MagicMock): Mock instance for get_executable_folder()
        """

        path = get_agent_executable_path(ORG_ID)
        mock_get_executable_folder.assert_called()
        self.assertEqual(path, f"/usr/local/bin/rewst_remote_agent_{ORG_ID}.macos.bin")

    @patch("config_module.config_io.os_type", "unsupported")
    @patch("logging.error")
    def test_get_agent_executable_path_unsupported(self, mock_error: MagicMock) -> None:
        """Test the get_agent_executable_path() function for Unsupported platform

        Args:
            mock_error (MagicMock): Mock instance for logging.error()
        """

        with self.assertRaises(SystemExit):
            get_agent_executable_path(ORG_ID)
        mock_error.assert_called()

    @patch("config_module.config_io.os_type", "windows")
    @patch(
        "config_module.config_io.get_executable_folder",
        return_value=f"C:\\Program Files\\RewstRemoteAgent\\{ORG_ID}\\",
    )
    def test_get_service_executable_path_windows(
        self, mock_get_executable_folder: MagicMock
    ) -> None:
        """Test the get_service_executable_path() function for Windows platform

        Args:
            mock_get_executable_folder (MagicMock): Mock instance for get_service_executable_path()
        """

        path = get_service_executable_path(ORG_ID)
        mock_get_executable_folder.assert_called()
        self.assertEqual(
            path,
            f"C:\\Program Files\\RewstRemoteAgent\\{ORG_ID}\\"
            + f"rewst_windows_service_{ORG_ID}.win.exe",
        )

    @patch("config_module.config_io.os_type", "linux")
    @patch("logging.info")
    def test_get_service_executable_path_linux(self, mock_info: MagicMock) -> None:
        """Test the get_service_executable_path() function for Linux platform

        Args:
            mock_info (MagicMock): Mock instance for logging.info()
        """

        path = get_service_executable_path(ORG_ID)
        mock_info.assert_called()
        self.assertEqual(path, None)

    @patch("config_module.config_io.os_type", "windows")
    @patch("logging.info")
    def test_get_logging_path_windows(self, mock_info: MagicMock) -> None:
        """Test the get_logging_path() function for Windows platform

        Args:
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        path = get_logging_path(ORG_ID)
        mock_info.assert_called()
        self.assertEqual(
            path, f"C:\\ProgramData\\RewstRemoteAgent\\{ORG_ID}\\logs\\rewst_agent.log"
        )

    @patch("config_module.config_io.os_type", "linux")
    @patch("logging.info")
    def test_get_logging_path_linux(self, mock_info: MagicMock) -> None:
        """Test the get_logging_path() function for Linux platform

        Args:
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        path = get_logging_path(ORG_ID)
        mock_info.assert_called()
        self.assertEqual(path, f"/var/log/rewst_remote_agent/{ORG_ID}/rewst_agent.log")

    @patch("config_module.config_io.os_type", "darwin")
    @patch("logging.info")
    def test_get_logging_path_darwin(self, mock_info: MagicMock) -> None:
        """Test the get_logging_path() function for Darwin platform

        Args:
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        path = get_logging_path(ORG_ID)
        mock_info.assert_called()
        self.assertEqual(path, f"/var/log/rewst_remote_agent/{ORG_ID}/rewst_agent.log")

    @patch("config_module.config_io.os_type", "unsupported")
    @patch("logging.error")
    def test_get_logging_path_unsupported(self, mock_error: MagicMock) -> None:
        """Test the get_logging_path() function for Unsupported platform

        Args:
            mock_error (MagicMock): Mock instance for logging.error() function
        """

        with self.assertRaises(SystemExit):
            get_logging_path(ORG_ID)
        mock_error.assert_called()

    @patch("config_module.config_io.os_type", "windows")
    @patch("logging.info")
    def test_get_config_file_path_windows(self, mock_info: MagicMock) -> None:
        """Test the get_config_file_path() function for Windows platform

        Args:
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        path = get_config_file_path(ORG_ID)
        mock_info.assert_called()
        self.assertEqual(
            path, f"C:\\ProgramData\\RewstRemoteAgent\\{ORG_ID}\\config.json"
        )

    @patch("config_module.config_io.os_type", "linux")
    @patch("logging.info")
    def test_get_config_file_path_linux(self, mock_info: MagicMock) -> None:
        """Test the get_config_file_path() function for Linux platform

        Args:
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        path = get_config_file_path(ORG_ID)
        mock_info.assert_called()
        self.assertEqual(path, f"/etc/rewst_remote_agent/{ORG_ID}/config.json")

    @patch("config_module.config_io.os_type", "darwin")
    @patch("logging.info")
    def test_get_config_file_path_darwin(self, mock_info: MagicMock) -> None:
        """Test the get_config_file_path() function for Darwin platform

        Args:
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        path = get_config_file_path(ORG_ID)
        mock_info.assert_called()
        self.assertEqual(
            path,
            os.path.expanduser(
                f"~/Library/Application Support/RewstRemoteAgent/{ORG_ID}/config.json"
            ),
        )

    @patch("config_module.config_io.os_type", "unsupported")
    @patch("logging.error")
    @patch("logging.info")
    def test_get_config_file_path_unsupported(
        self, mock_error: MagicMock, mock_info: MagicMock
    ) -> None:
        """Test the get_config_file_path() function for Unsupported platform

        Args:
            mock_error (MagicMock): Mock instance for logging.error() function
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        with self.assertRaises(SystemExit):
            get_config_file_path(ORG_ID)
        mock_error.assert_called()
        mock_info.assert_called()

    @patch("config_module.config_io.os_type", "windows")
    @patch("logging.error")
    @patch("logging.info")
    @patch("os.makedirs", side_effect=OSError())
    def test_get_config_file_path_exception(
        self, mock_makedirs: MagicMock, mock_info: MagicMock, mock_error: MagicMock
    ) -> None:
        """Test the get_config_file_path() function for the case
        when the creation of config directory fails.

        Args:
            mock_error (MagicMock): Mock instance for logging.error() function
            mock_info (MagicMock): Mock instance for logging.info() function
        """

        with self.assertRaises(OSError):
            get_config_file_path(ORG_ID)
        mock_error.assert_called()
        mock_info.assert_called()
        mock_makedirs.assert_called()

    @patch("builtins.open", new_callable=mock.mock_open)
    @patch("config_module.config_io.get_config_file_path", return_value="config.json")
    @patch("logging.info")
    def test_save_configuration(
        self,
        mock_info: MagicMock,
        mock_get_config_file_path: MagicMock,
        mock_open: MagicMock,
    ) -> None:
        """Test the save_configuration() function

        Args:
            mock_info (MagicMock): Mock instance for logging.info()
            mock_get_config_file_path (MagicMock): Mock instance for get_config_file_path()
            mock_open (MagicMock): Mock instance for open()
        """

        config_data = {"rewst_org_id": ORG_ID, "key": "value"}
        save_configuration(config_data)
        mock_open.assert_called_once_with("config.json", "w")
        mock_get_config_file_path.assert_called()
        mock_info.assert_called()

    @patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data='{"rewst_org_id": "test_org", "key": "value"}',
    )
    @patch("config_module.config_io.get_config_file_path", return_value="config.json")
    @patch("logging.info")
    def test_load_configuration(
        self,
        mock_info: MagicMock,
        mock_get_config_file_path: MagicMock,
        mock_open: MagicMock,
    ) -> None:
        """Test the load_configuration() function

        Args:
            mock_info (MagicMock): Mock instance for logging.info()
            mock_get_config_file_path (MagicMock): Mock instance for get_config_file_path()
            mock_open (MagicMock): Mock instance for open()
        """

        config = load_configuration(ORG_ID)
        self.assertEqual(config, {"rewst_org_id": "test_org", "key": "value"})
        mock_get_config_file_path.assert_called()
        mock_open.assert_called()
        mock_info.assert_called()

    @patch("builtins.open", side_effect=FileNotFoundError())
    @patch("config_module.config_io.get_config_file_path", return_value="config.json")
    @patch("logging.exception")
    def test_load_configuration_not_found(
        self,
        mock_exception: MagicMock,
        mock_get_config_file_path: MagicMock,
        mock_open: MagicMock,
    ) -> None:
        """Test the load_configuration() function when the config file is not found

        Args:
            mock_exception (MagicMock): Mock instance for logging.exception()
            mock_get_config_file_path (MagicMock): Mock instance for get_config_file_path()
            mock_open (MagicMock): Mock instance for open()
        """

        self.assertIsNone(load_configuration(ORG_ID))
        mock_get_config_file_path.assert_called()
        mock_open.assert_called()
        mock_exception.assert_called()

    def test_get_org_id_from_executable_name(self) -> None:
        """Test the get_org_id_from_executable_name() function"""

        args = [f"rewst_remote_agent_{ORG_ID}.win.exe"]
        org_id = get_org_id_from_executable_name(args)
        self.assertEqual(org_id, ORG_ID)

    def test_get_org_id_from_executable_name_unmatched(self) -> None:
        """Test the get_org_id_from_executable_name() function
        when the name doesn't match the pattern"""

        args = [f"xewst_remote_agent_{ORG_ID}.win.exe"]
        org_id = get_org_id_from_executable_name(args)
        self.assertEqual(org_id, False)

    @patch("config_module.config_io.get_logging_path", return_value="test.log")
    @patch("os.makedirs")
    @patch("logging.basicConfig")
    @patch("builtins.print")
    def test_setup_file_logging(
        self,
        mock_print: MagicMock,
        mock_basic_config: MagicMock,
        mock_makedirs: MagicMock,
        mock_logging_path: MagicMock,
    ):
        """Test the setup_file_logging() functio

        Args:
            mock_print (MagicMock): Mock instance for print()
            mock_basic_config (MagicMock): Mock instance for logging.basicConfig()
            mock_makedirs (MagicMock): Mock instance for makedirs()
            mock_logging_path (MagicMock): Mock instace for get_logging_path()
        """

        success = setup_file_logging(ORG_ID)
        self.assertTrue(success)
        mock_basic_config.assert_called()
        mock_makedirs.assert_called()
        mock_logging_path.assert_called()
        mock_print.assert_called()

    @patch("config_module.config_io.get_logging_path", return_value="test.log")
    @patch("os.makedirs", side_effect=OSError())
    @patch("builtins.print")
    def test_setup_file_logging_error(
        self,
        mock_print: MagicMock,
        mock_makedirs: MagicMock,
        mock_logging_path: MagicMock,
    ):
        """Test the setup_file_logging() function when the makedirs() failed

        Args:
            mock_print (MagicMock): Mock instance for print()
            mock_makedirs (MagicMock): Mock instance for makedirs()
            mock_logging_path (MagicMock): Mock instace for get_logging_path()
        """

        self.assertFalse(setup_file_logging(ORG_ID))
        mock_makedirs.assert_called()
        mock_logging_path.assert_called()
        mock_print.assert_called()


if __name__ == "__main__":
    unittest.main()
