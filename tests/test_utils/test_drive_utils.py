
from unittest.mock import Mock, patch

import pytest
from google.oauth2.credentials import Credentials

from src.utils.drive_utils import SCOPES, CredentialsError, DriveConfig, DriveCredentials, DriveFile, FilesServiceFacade, ServiceGenerator, SheetServiceFacade, get_service_generator, get_sheet_service, get_files_service, get_document_id


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
def mock_credentials(mocker):
    creds_mock = mocker.patch("src.utils.drive_utils.Credentials.from_authorized_user_info")
    creds_mock.return_value = Mock(spec=Credentials)
    return creds_mock


def test_valid_credentials(mock_credentials, test_config):
    mock_credentials.return_value.valid = True
    drive_creds = DriveCredentials(test_config)

    creds = drive_creds.get_drive_credentials()
    assert creds.valid
    mock_credentials.assert_called_once_with(drive_creds.token_dict, SCOPES)


def test_expired_credentials_with_refresh(mock_credentials, test_config):
    mock_credentials.return_value.valid = False
    mock_credentials.return_value.to_json.return_value = '{"valid": true}'
    drive_creds = DriveCredentials(test_config)

    creds = drive_creds.get_drive_credentials()
    assert not creds.valid
    assert drive_creds.token_dict == {"valid": True}
    mock_credentials.return_value.refresh.assert_called_once()


def test_invalid_credentials(mock_credentials, test_config):
    mock_credentials.return_value.valid = False
    mock_credentials.return_value.expired = False
    drive_creds = DriveCredentials(test_config)

    with pytest.raises(CredentialsError):
        drive_creds.get_drive_credentials()


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

def test_files_service_facade_list_files():
    service = Mock()
    service.return_value.execute.return_value = {
        "files": [{
            "id": "1", 
            "name": "file1", 
            "mimeType": "type1", 
            "modifiedTime": "time1",
            "webViewLink": "asd"}]}
    files_service = FilesServiceFacade(service)

    result = files_service.get_file("1")
    service.assert_called_once_with(
        pageSize=50, 
        fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)", 
        q="id = '1'")

    assert result == DriveFile(**{"id": "1", "name": "file1", "mimeType": "type1", 
                               "modifiedTime": "time1", "webViewLink": "asd"})


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

    result = service_gen.get_service("service_name", "v4")
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


def test_service_generator_get_files_service(mock_build, mock_drive_credentials):
    service = Mock()
    mock_build.return_value = service
    service_gen = ServiceGenerator(mock_drive_credentials)

    result = service_gen.get_files_service()
    assert isinstance(result, FilesServiceFacade)
    assert mock_build.call_count == 1
    mock_build.assert_called_once_with("drive", "v3", credentials={"valid": True})

    assert service.files.call_count == 1


def test_get_service_generator(mocker, test_config):
    mock_drive_credentials = mocker.patch("src.utils.drive_utils.DriveCredentials")
    mock_drive_credentials.return_value = mock_drive_credentials

    result = get_service_generator(test_config)

    mock_drive_credentials.assert_called_once_with(test_config)
    assert isinstance(result, ServiceGenerator)
    assert result.drive_creds == mock_drive_credentials

def test_get_sheet_service(mocker, test_config):
    sheet_service_mock = Mock(spec=SheetServiceFacade)
    mock_service_gen = mocker.patch("src.utils.drive_utils.get_service_generator")
    mock_service_gen.return_value = mock_service_gen
    mock_service_gen.get_sheet_service.return_value = sheet_service_mock

    result = get_sheet_service(test_config)

    mock_service_gen.assert_called_once_with(test_config)
    mock_service_gen.get_sheet_service.assert_called_once()
    assert result == sheet_service_mock
    assert isinstance(result, SheetServiceFacade)

def test_get_files_service(mocker, test_config):
    files_service_mock = Mock(spec=FilesServiceFacade)
    mock_service_gen = mocker.patch("src.utils.drive_utils.get_service_generator")
    mock_service_gen.return_value = mock_service_gen
    mock_service_gen.get_files_service.return_value = files_service_mock

    result = get_files_service(test_config)

    mock_service_gen.assert_called_once_with(test_config)
    mock_service_gen.get_files_service.assert_called_once()
    assert result == files_service_mock
    assert isinstance(result, FilesServiceFacade)

def test_get_document_id(mocker, test_config):
    url = "https://docs.google.com/document/d/1/edit"
    result = get_document_id(url)
    assert result == "1"

    url = "https://docs.google.com/document/d/1/"
    result = get_document_id(url)
    assert result == "1"

    url = "https://docs.google.com/document/d/1/other"
    result = get_document_id(url)
    assert result == "1"

    with pytest.raises(ValueError):
        get_document_id("https://docs.google.com/spreadsheet/d/1/edit")
