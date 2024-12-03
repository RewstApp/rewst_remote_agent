""" Global helper functions for testing """

from pytest_mock import MockerFixture


def mock_platform(mocker: MockerFixture, platform: str) -> None:
    """
    Mock the os_type variable for all scripts.

    Args:
        mocker (MockerFixture): Mocker fixture instance.
        platform (str): Platform name in lowercase (e.g. windows, linux, darwin).
    """
    mocker.patch("config_module.config_io.os_type", platform)
    mocker.patch("iot_hub_module.connection_management.os_type", platform)
    mocker.patch("service_module.service_management.os_type", platform)
