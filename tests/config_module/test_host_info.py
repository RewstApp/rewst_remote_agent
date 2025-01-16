"""Module for testing the host_info module"""
import subprocess
import unittest
from unittest.mock import patch, MagicMock
from config_module.host_info import (
    get_mac_address,
    run_powershell_command,
    is_domain_controller,
    get_ad_domain_name,
    get_entra_domain,
    is_entra_connect_server,
    is_service_running,
    build_host_tags
)


class TestHostInfo(unittest.TestCase):
    """Test class for host_info unit tests"""    

    @patch("psutil.net_if_addrs")
    @patch("uuid.getnode")
    def test_get_mac_address(self, mock_getnode, mock_net):
        mock_net.items.return_value = []
        # Mocking the UUID return value to a fixed value for testing
        mock_getnode.return_value = 123456789012345
        mac_address = get_mac_address()
        # Expected MAC address format
        self.assertEqual(mac_address, "7048860ddf79")

    @patch("config_module.host_info.subprocess.run")
    def test_run_powershell_command_success(self, mock_subprocess):
        # Mocking a successful PowerShell command execution
        mock_subprocess.return_value = MagicMock(stdout="Success")
        result = run_powershell_command("Test-Command")
        self.assertEqual(result, "Success")

    @patch("config_module.host_info.subprocess.run")
    def test_run_powershell_command_failure(self, mock_subprocess):
        # Simulate a failure in command execution
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
        result = run_powershell_command("Test-Command")
        self.assertIsNone(result)

    @patch("config_module.host_info.run_powershell_command")
    def test_is_domain_controller_true(self, mock_run_powershell_command):
        # Simulate output indicating the machine is a domain controller
        mock_run_powershell_command.return_value = "True"
        result = is_domain_controller()
        self.assertTrue(result)

    @patch("config_module.host_info.run_powershell_command")
    def test_is_domain_controller_false(self, mock_run_powershell_command):
        # Simulate output indicating the machine is not a domain controller
        mock_run_powershell_command.return_value = "False"
        result = is_domain_controller()
        self.assertFalse(result)

    @patch("config_module.host_info.run_powershell_command")
    def test_get_ad_domain_name(self, mock_run_powershell_command):
        # Simulate retrieving the AD domain name
        mock_run_powershell_command.return_value = "example.com"
        domain_name = get_ad_domain_name()
        self.assertEqual(domain_name, "example.com")

    @patch("config_module.host_info.subprocess.run")
    @patch("config_module.host_info.platform.system", return_value="Windows")
    def test_get_entra_domain_success(self, mock_platform, mock_subprocess):
        # Simulate successful dsregcmd command
        mock_subprocess.return_value = MagicMock(
            stdout="AzureAdJoined: YES\nDomainName: entra.example.com"
        )
        domain_name = get_entra_domain()
        self.assertEqual(domain_name, "entra.example.com")

    @patch("config_module.host_info.subprocess.run")
    @patch("config_module.host_info.platform.system", return_value="Linux")
    def test_get_entra_domain_failure(self, mock_platform, mock_subprocess):
        domain_name = get_entra_domain()
        self.assertIsNone(domain_name)

    @patch("psutil.win_service_iter")
    @patch("config_module.host_info.platform.system", return_value="Windows")
    def test_is_entra_connect_server_true(self, mock_platform, mock_service_iter):
        # Mock service names to simulate a running Entra Connect service
        mock_service = MagicMock()
        mock_service.name.return_value = "ADSync"
        mock_service_iter.return_value = [mock_service]

        result = is_entra_connect_server()
        self.assertTrue(result)

    @patch("config_module.host_info.psutil")
    @patch("config_module.host_info.platform.system", return_value="Linux")
    def test_is_entra_connect_server_false(self, mock_platform, mock_psutil):
        result = is_entra_connect_server()
        self.assertFalse(result)

    @patch("psutil.win_service_iter")
    @patch("config_module.host_info.platform.system", return_value="Windows")
    def test_is_service_running_true(self, mock_platform, mock_service_iter):
        # Simulate a running service
        mock_service = MagicMock()
        mock_service.name.return_value = "ADSync"
        mock_service_iter.return_value = [mock_service]

        result = is_service_running("ADSync")
        self.assertTrue(result)

    @patch("config_module.host_info.psutil")
    def test_is_service_running_false(self, mock_psutil):
        # Simulate no running service by returning an empty iterator
        mock_psutil.win_service_iter.return_value = []
        result = is_service_running("NonExistentService")
        self.assertFalse(result)

    @patch("config_module.host_info.socket.gethostname", return_value="test-host")
    @patch("config_module.host_info.get_mac_address", return_value="ABCDEF123456")
    @patch("config_module.host_info.platform.system", return_value="Windows")
    @patch("config_module.host_info.platform.platform", return_value="Windows-10")
    @patch("config_module.host_info.platform.processor", return_value="Intel")
    @patch("config_module.host_info.psutil")
    @patch("config_module.host_info.run_powershell_command", return_value="example.com")
    @patch("config_module.host_info.get_ad_domain_name", return_value="example.com")
    @patch("config_module.host_info.is_domain_controller", return_value=True)
    @patch("config_module.host_info.is_entra_connect_server", return_value=True)
    @patch("config_module.host_info.get_entra_domain", return_value="entra.example.com")
    def test_build_host_tags(
        self,
        mock_get_entra_domain,
        mock_is_entra_connect_server,
        mock_is_dc,
        mock_get_ad_domain_name,
        mock_run_powershell_command,
        mock_psutil,
        mock_processor,
        mock_platform,
        mock_system,
        mock_mac_address,
        mock_gethostname,
    ):
        # Set up a mock for psutil virtual memory
        mock_psutil.virtual_memory.return_value = MagicMock(total=16 * 1024**3)  # 16GB
        # Call build_host_tags with a test org ID
        host_tags = build_host_tags("test_org")

        # Assertions to verify the collected host info
        self.assertEqual(host_tags["hostname"], "test-host")
        self.assertEqual(host_tags["mac_address"], "ABCDEF123456")
        self.assertEqual(host_tags["operating_system"], "Windows-10")
        self.assertEqual(host_tags["cpu_model"], "Intel")
        self.assertEqual(host_tags["ram_gb"], 16)
        self.assertEqual(host_tags["ad_domain"], "example.com")
        self.assertTrue(host_tags["is_ad_domain_controller"])
        self.assertTrue(host_tags["is_entra_connect_server"])
        self.assertEqual(host_tags["entra_domain"], "entra.example.com")
        self.assertEqual(host_tags["org_id"], "test_org")


if __name__ == "__main__":
    unittest.main()
