"""
Tests for error handling module
"""

import uuid
import logging
import pytest
from pytest_mock import MockerFixture
from iot_hub_module.error_handling import (
    setup_logging, log_error, log_info
)

# Constants
MODULE = "iot_hub_module.error_handling"
ORG_ID = str(uuid.uuid4())
SERVICE_NAME = f"RewstRemoteAgent_{ORG_ID}"
EXECUTABLE_NAME = f"rewst_remote_agent_{ORG_ID}"

@pytest.mark.parametrize("platform", ("Windows", "Linux", "Darwin"))
def test_setup_logging(mocker: MockerFixture, platform: str) -> None:
    """
    Test setup_logging().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocker.patch("platform.system", return_value=platform)
    mocker.patch("logging.FileHandler")

    assert isinstance(setup_logging(SERVICE_NAME), logging.Logger)

def test_log_error(mocker: MockerFixture) -> None:
    """
    Test setup_logging().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocked_logger = mocker.MagicMock()

    assert log_error(mocked_logger, "ERROR") is None

    mocked_logger.error.assert_called_with("ERROR")

def test_log_info(mocker: MockerFixture) -> None:
    """
    Test setup_logging().

    Args:
        mocker (MockerFixture): Fixture instance for mocking.
    """
    mocked_logger = mocker.MagicMock()

    assert log_info(mocked_logger, "INFO") is None

    mocked_logger.info.assert_called_with("INFO")