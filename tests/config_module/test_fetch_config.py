"""Module for testing the fetch_config.py module"""

import unittest
from unittest import mock
import httpx
from config_module.fetch_config import (
    fetch_configuration,
)


class TestFetchConfig(unittest.IsolatedAsyncioTestCase):
    """Test class for fetch_config.py module"""

    async def test_fetch_configuration_successful(self):
        """Test a successful configuration fetch with all required keys."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "configuration": {
                "azure_iot_hub_host": "test_host",
                "device_id": "test_device",
                "shared_access_key": "test_key",
                "rewst_engine_host": "test_engine",
                "rewst_org_id": "test_org",
            }
        }

        with mock.patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await fetch_configuration("http://test_url", secret="test_secret")
            self.assertIsNotNone(result)
            self.assertIn("azure_iot_hub_host", result)

    async def test_fetch_configuration_missing_required_keys(self):
        """Test configuration fetch when response is missing required keys."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "configuration": {
                "device_id": "test_device",
                "rewst_org_id": "test_org",
            }
        }

        with mock.patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await fetch_configuration(
                "http://test_url", secret="test_secret", retry_intervals=((0, 1))
            )
            self.assertIsNone(result)

    async def test_fetch_configuration_retry_on_timeout(self):
        """Test that fetch_configuration retries on timeout."""
        with mock.patch(
            "httpx.AsyncClient.post",
            side_effect=httpx.TimeoutException("Request timeout"),
        ), mock.patch("asyncio.sleep", return_value=None) as mock_sleep:
            result = await fetch_configuration(
                "http://test_url", secret="test_secret", retry_intervals=((10, 2))
            )
            self.assertIsNone(result)
            self.assertTrue(mock_sleep.called)

    async def test_fetch_configuration_network_error(self):
        """Test fetch_configuration with network errors that trigger retries."""
        with mock.patch(
            "httpx.AsyncClient.post", side_effect=httpx.RequestError("Network error")
        ), mock.patch("asyncio.sleep", return_value=None) as mock_sleep:
            result = await fetch_configuration(
                "http://test_url", secret="test_secret", retry_intervals=((10, 2))
            )
            self.assertIsNone(result)
            self.assertTrue(mock_sleep.called)

    async def test_fetch_configuration_registration_in_progress(self):
        """Test fetch_configuration with a 303 status code (registration in progress)."""
        mock_response = mock.Mock()
        mock_response.status_code = 303

        with mock.patch(
            "httpx.AsyncClient.post", return_value=mock_response
        ), mock.patch("asyncio.sleep", return_value=None) as mock_sleep:
            result = await fetch_configuration(
                "http://test_url", secret="test_secret", retry_intervals=[(10, 2)]
            )
            self.assertIsNone(result)
            self.assertTrue(mock_sleep.called)

    async def test_fetch_configuration_unauthorized(self):
        """Test fetch_configuration with unauthorized access (400/401 errors)."""
        mock_response = mock.Mock()
        mock_response.status_code = 401

        with mock.patch("httpx.AsyncClient.post", return_value=mock_response):
            with self.assertLogs(level="ERROR") as log:
                result = await fetch_configuration(
                    "http://test_url", secret="test_secret", retry_intervals=[(10, 2)]
                )
                self.assertIsNone(result)
                self.assertIn("Not authorized", log.output[0])

    async def test_fetch_configuration_max_retries_exceeded(self):
        """Test that fetch_configuration stops retrying after max retries are reached."""
        mock_response = mock.Mock()
        mock_response.status_code = 500

        with mock.patch(
            "httpx.AsyncClient.post", return_value=mock_response
        ), mock.patch("asyncio.sleep", return_value=None) as mock_sleep:
            result = await fetch_configuration(
                "http://test_url", secret="test_secret", retry_intervals=((10, 3))
            )
            self.assertIsNone(result)
            self.assertGreaterEqual(
                mock_sleep.call_count, 3
            )  # Checks if retry logic occurred


if __name__ == "__main__":
    unittest.main()
