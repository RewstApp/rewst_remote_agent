import os
import pytest
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
    setup_file_logging
)

# Test get_executable_folder
@pytest.mark.parametrize("os_type, org_id, expected_path", [
    ("windows", "test_org", r"ProgramFiles\RewstRemoteAgent\test_org\\"),
    ("linux", "test_org", "/usr/local/bin/"),
    ("darwin", "test_org", "~/Library/Application Support/RewstRemoteAgent/test_org/")
])
@patch("platform.system")
@patch("os.environ.get")
def test_get_executable_folder(mock_env, mock_system, os_type, org_id, expected_path):
    mock_system.return_value = os_type
    mock_env.return_value = "ProgramFiles" if os_type == "windows" else None
    path = get_executable_folder(org_id)
    assert path.endswith(expected_path)


# Test get_service_manager_path
@pytest.mark.parametrize("os_type, org_id, expected_filename", [
    ("windows", "test_org", "rewst_service_manager.win_test_org.exe"),
    ("linux", "test_org", "rewst_service_manager.linux_test_org.bin"),
    ("darwin", "test_org", "rewst_service_manager.macos_test_org.bin")
])
@patch("config_module.get_executable_folder")
@patch("config_module.os_type", new_callable=lambda: "patch")
def test_get_service_manager_path(mock_folder, os_type, org_id, expected_filename):
    mock_folder.return_value = "/mock_path/"
    path = get_service_manager_path(org_id)
    assert path.endswith(expected_filename)


# Test get_logging_path
@patch("config_module.site_config_dir")
@patch("config_module.os_type", new_callable=lambda: "windows")
def test_get_logging_path(mock_site_dir):
    mock_site_dir.return_value = "C:\\Config"
    path = get_logging_path("test_org")
    assert "C:\\Config\\RewstRemoteAgent\\test_org\\logs\\rewst_agent.log" in path


# Test save_configuration and load_configuration
@patch("config_module.get_config_file_path")
@patch("builtins.open", new_callable=MagicMock)
def test_save_and_load_configuration(mock_open, mock_get_path):
    mock_get_path.return_value = "/mock/path/config.json"
    mock_open.return_value.__enter__.return_value = MagicMock()

    config_data = {"rewst_org_id": "test_org", "config_key": "config_value"}

    # Test save_configuration
    save_configuration(config_data)
    mock_open.assert_called_once_with("/mock/path/config.json", "w")

    # Test load_configuration
    with patch("json.load", return_value=config_data):
        loaded_config = load_configuration("test_org")
        assert loaded_config == config_data


# Test get_org_id_from_executable_name
def test_get_org_id_from_executable_name():
    commandline_args = ["/path/to/rewst_remote_agent_test_org.linux.bin"]
    org_id = get_org_id_from_executable_name(commandline_args)
    assert org_id == "test_org"


# Test setup_file_logging
@patch("config_module.get_logging_path", return_value="/mock/log/path/rewst_agent.log")
@patch("os.makedirs")
@patch("logging.basicConfig")
@patch("logging.root")
def test_setup_file_logging(mock_root, mock_basic_config, mock_makedirs, mock_get_log_path):
    mock_root.handlers = []
    setup_file_logging("test_org")
    mock_makedirs.assert_called_once_with("/mock/log/path", exist_ok=True)
    assert mock_basic_config.called
    assert mock_root.handlers
