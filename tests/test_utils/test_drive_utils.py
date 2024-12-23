
from unittest.mock import Mock, patch

import pytest
from google.oauth2.credentials import Credentials

from src.utils.drive_utils import SCOPES, CredentialsError, DriveConfig, DriveCredentials, ServiceGenerator, SheetServiceFacade


def test_sheet_service_facade_get():
    service = Mock()
    service.values().get().execute.return_value = {"values": [["A1", "B1"], ["A2", "B2"]]}

    sheet_service = SheetServiceFacade(service)

    result = sheet_service.get("spreadsheet_id", "range")
    assert result == [["A1", "B1"], ["A2", "B2"]]

def test_sheet_service_facade_update():
    service = Mock()
    sheet_service = SheetServiceFacade(service)
    sheet_service.update("spreadsheet_id", "range", [["1", "2"], ["3", "4"]])
    service.values().update.assert_called_once_with(
        spreadsheetId="spreadsheet_id",
        range="range",
        valueInputOption="USER_ENTERED",
        body={"values": [["1", "2"], ["3", "4"]]},
    )


@pytest.fixture
def test_config():
    return DriveConfig(
        DRIVE_CLIENT_ID="your_client_id",
        DRIVE_PROJECT_ID="your_project_id",
        CLIENT_SECRET="your_client_secret",
        DRIVE_TOKEN="valid_token",
        DRIVE_REFRESH_TOKEN="valid_refresh_token"
    )


@pytest.fixture
def mock_credentials_gen():
    with patch('google.oauth2.credentials.Credentials.from_authorized_user_info') as mock_from_auth_user_info:
        yield mock_from_auth_user_info


def test_valid_credentials(mock_credentials_gen, test_config):
    drive_creds = DriveCredentials(test_config)
    mock_credentials_gen.return_value = Mock(spec=Credentials)
    mock_credentials_gen.return_value.valid = True

    creds = drive_creds.get_drive_credentials()
    assert creds.valid
    mock_credentials_gen.assert_called_once_with(drive_creds.token_dict, SCOPES)


def test_expired_credentials_with_refresh(mock_credentials_gen, test_config):
    drive_creds = DriveCredentials(test_config)
    mock_credentials_gen.return_value = Mock(spec=Credentials)
    mock_credentials_gen.return_value.valid = False
    mock_credentials_gen.return_value.to_json.return_value = '{"valid": true}'

    creds = drive_creds.get_drive_credentials()
    assert not creds.valid
    assert drive_creds.token_dict == {"valid": True}
    mock_credentials_gen.return_value.refresh.assert_called_once()


def test_invalid_credentials(mock_credentials_gen, test_config):
    drive_creds = DriveCredentials(test_config)
    mock_credentials_gen.return_value = Mock(spec=Credentials)
    mock_credentials_gen.return_value.valid = False
    mock_credentials_gen.return_value.expired = False
    
    with pytest.raises(CredentialsError):
        drive_creds.get_drive_credentials()


@pytest.fixture
def mock_drive_credentials():
    m = Mock(spec=DriveCredentials)
    m.get_drive_credentials.return_value = {"valid": True}
    return m


@pytest.fixture
def mock_build():
    with patch("src.utils.drive_utils.build") as mock_builds:
        yield mock_builds


def test_service_generator_get_service(mock_build, mock_drive_credentials):
    service = Mock()
    mock_build.return_value = service
    service_gen = ServiceGenerator(mock_drive_credentials)

    result = service_gen.get_service("service_name")
    assert result == service
    mock_drive_credentials.get_drive_credentials.assert_called_once()
    mock_build.assert_called_once_with("service_name", "v4", credentials={"valid": True})


def test_service_generator_get_sheet_service(mock_build, mock_drive_credentials):
    service = Mock()
    mock_build.return_value = service
    service_gen = ServiceGenerator(mock_drive_credentials)

    result = service_gen.get_sheet_service()
    assert isinstance(result, SheetServiceFacade)
    assert mock_build.call_count == 1
    mock_build.assert_called_once_with("sheets", "v4", credentials={"valid": True})

    assert service.spreadsheets.call_count == 1