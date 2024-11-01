# test_fetch_configuration.py

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from config_module.fetch_config import *

REQUIRED_KEYS = [
    "azure_iot_hub_host",
    "device_id",
    "shared_access_key",
    "rewst_engine_host",
    "rewst_org_id",
]

@pytest.mark.asyncio
@patch("fetch_configuration_module.build_host_tags", return_value={"mock": "host_info"})
@patch("fetch_configuration_module.httpx.AsyncClient")
async def test_fetch_configuration_success(mock_client, mock_build_host_tags):
    # Mock response for a successful configuration fetch with required keys
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"configuration": {key: "value" for key in REQUIRED_KEYS}}
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

    config_url = "https://test-config-url.com"
    config_data = await fetch_configuration(config_url, secret="test_secret", org_id="test_org")

    assert config_data is not None
    assert all(key in config_data for key in REQUIRED_KEYS)

@pytest.mark.asyncio
@patch("fetch_configuration_module.build_host_tags", return_value={"mock": "host_info"})
@patch("fetch_configuration_module.httpx.AsyncClient")
async def test_fetch_configuration_missing_keys(mock_client, mock_build_host_tags):
    # Mock response with missing keys in configuration data
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"configuration": {"azure_iot_hub_host": "value"}}
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

    config_url = "https://test-config-url.com"
    config_data = await fetch_configuration(config_url, secret="test_secret", org_id="test_org")

    assert config_data is None  # Expect None since required keys are missing

@pytest.mark.asyncio
@patch("fetch_configuration_module.build_host_tags", return_value={"mock": "host_info"})
@patch("fetch_configuration_module.httpx.AsyncClient")
async def test_fetch_configuration_retry_on_timeout(mock_client, mock_build_host_tags):
    # Simulate timeout exception to test retry mechanism
    mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
    config_url = "https://test-config-url.com"
    retries = 0

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        config_data = await fetch_configuration(config_url, secret="test_secret", org_id="test_org")
        assert config_data is None  # Expect None after exhausting retries
        assert mock_sleep.await_count > 0  # Check if retries occurred

@pytest.mark.asyncio
@patch("fetch_configuration_module.build_host_tags", return_value={"mock": "host_info"})
@patch("fetch_configuration_module.httpx.AsyncClient")
async def test_fetch_configuration_status_303(mock_client, mock_build_host_tags):
    # Mock response with a 303 status code to test registration wait message
    mock_response = AsyncMock()
    mock_response.status_code = 303
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

    config_url = "https://test-config-url.com"
    with patch("logging.info") as mock_log_info:
        await fetch_configuration(config_url, secret="test_secret", org_id="test_org")
        mock_log_info.assert_any_call("Waiting while Rewst processes Agent Registration...")

@pytest.mark.asyncio
@patch("fetch_configuration_module.build_host_tags", return_value={"mock": "host_info"})
@patch("fetch_configuration_module.httpx.AsyncClient")
async def test_fetch_configuration_unauthorized(mock_client, mock_build_host_tags):
    # Mock response with a 401 status code to test unauthorized message
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

    config_url = "https://test-config-url.com"
    with patch("logging.error") as mock_log_error:
        await fetch_configuration(config_url, secret="invalid_secret", org_id="test_org")
        mock_log_error.assert_any_call("Attempt 1: Not authorized. Check your config secret.")
