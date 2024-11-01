# test_host_info.py

import pytest
from unittest.mock import patch, MagicMock
from config_module.host_info import (
    get_mac_address,
    run_powershell_command,
    is_domain_controller,
    get_ad_domain_name,
    get_entra_domain,
    is_entra_connect_server,
    is_service_running,
    build_host_tags,
)

@pytest.fixture
def mock_psutil():
    with patch("host_info.psutil") as mock_psutil:
        yield mock_psutil

@pytest.fixture
def mock_platform():
    with patch("host_info.platform") as mock_platform:
        yield mock_platform

@pytest.fixture
def mock_subprocess():
    with patch("host_info.subprocess.run") as mock_subprocess:
        yield mock_subprocess

@pytest.fixture
def mock_socket():
    with patch("host_info.socket") as mock_socket:
        yield mock_socket


def test_get_mac_address():
    mac_address = get_mac_address()
    assert isinstance(mac_address, str)
    assert len(mac_address) == 12  # Check MAC address length without colons


def test_run_powershell_command_success(mock_subprocess):
    # Mocking a successful PowerShell command execution
    mock_subprocess.return_value = MagicMock(stdout="Success")
    result = run_powershell_command("Test-Command")
    assert result == "Success"


def test_run_powershell_command_failure(mock_subprocess):
    # Simulate a failure in command execution
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
    result = run_powershell_command("Test-Command")
    assert result is None


def test_is_domain_controller_true(mock_subprocess):
    # Simulate output indicating the machine is a domain controller
    mock_subprocess.return_value = MagicMock(stdout="True")
    result = is_domain_controller()
    assert result is True


def test_is_domain_controller_false(mock_subprocess):
    # Simulate output indicating the machine is not a domain controller
    mock_subprocess.return_value = MagicMock(stdout="False")
    result = is_domain_controller()
    assert result is False


def test_get_ad_domain_name(mock_subprocess):
    # Simulate retrieving the AD domain name
    mock_subprocess.return_value = MagicMock(stdout="example.com")
    domain_name = get_ad_domain_name()
    assert domain_name == "example.com"


def test_get_entra_domain_success(mock_subprocess, mock_platform):
    # Mock platform to return Windows
    mock_platform.system.return_value = "Windows"
    # Simulate successful dsregcmd command
    mock_subprocess.return_value = MagicMock(stdout="AzureAdJoined: YES\nDomainName: entra.example.com")
    domain_name = get_entra_domain()
    assert domain_name == "entra.example.com"


def test_get_entra_domain_failure(mock_subprocess, mock_platform):
    # Mock platform to return non-Windows
    mock_platform.system.return_value = "Linux"
    domain_name = get_entra_domain()
    assert domain_name is None


def test_is_entra_connect_server_true(mock_psutil, mock_platform):
    # Mock platform to return Windows
    mock_platform.system.return_value = "Windows"
    # Mock service names to simulate a running Entra Connect service
    mock_psutil.win_service_iter.return_value = [MagicMock(name="ADSync")]
    result = is_entra_connect_server()
    assert result is True


def test_is_entra_connect_server_false(mock_psutil, mock_platform):
    # Mock platform to return non-Windows
    mock_platform.system.return_value = "Linux"
    result = is_entra_connect_server()
    assert result is False


def test_is_service_running_true(mock_psutil, mock_platform):
    # Mock platform to return Windows
    mock_platform.system.return_value = "Windows"
    # Simulate a running service
    mock_psutil.win_service_iter.return_value = [MagicMock(name="ADSync")]
    result = is_service_running("ADSync")
    assert result is True


def test_is_service_running_false(mock_psutil, mock_platform):
    # Simulate no running service by returning an empty iterator
    mock_psutil.win_service_iter.return_value = []
    result = is_service_running("NonExistentService")
    assert result is False


def test_build_host_tags(mock_platform, mock_psutil, mock_socket, mock_subprocess):
    # Mock platform details and psutil information
    mock_platform.system.return_value = "Windows"
    mock_platform.platform.return_value = "Windows-10"
    mock_platform.processor.return_value = "Intel"
    mock_socket.gethostname.return_value = "test-host"
    mock_psutil.virtual_memory.return_value = MagicMock(total=16 * 1024**3)  # 16GB
    mock_subprocess.return_value = MagicMock(stdout="example.com")

    # Patch other dependent functions
    with patch("host_info.get_mac_address", return_value="ABCDEF123456"):
        with patch("host_info.is_domain_controller", return_value=True):
            with patch("host_info.get_ad_domain_name", return_value="example.com"):
                with patch("host_info.is_entra_connect_server", return_value=True):
                    with patch("host_info.get_entra_domain", return_value="entra.example.com"):
                        host_tags = build_host_tags("test_org")

    # Assertions to verify the collected host info
    assert host_tags["hostname"] == "test-host"
    assert host_tags["mac_address"] == "ABCDEF123456"
    assert host_tags["operating_system"] == "Windows-10"
    assert host_tags["cpu_model"] == "Intel"
    assert host_tags["ram_gb"] == 16
    assert host_tags["ad_domain"] == "example.com"
    assert host_tags["is_ad_domain_controller"] is True
    assert host_tags["is_entra_connect_server"] is True
    assert host_tags["entra_domain"] == "entra.example.com"
    assert host_tags["org_id"] == "test_org"
