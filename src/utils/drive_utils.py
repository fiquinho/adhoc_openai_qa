import json
from typing import Any, Literal
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel


class DriveConfig(BaseModel):
    DRIVE_CLIENT_ID: str
    DRIVE_PROJECT_ID: str
    CLIENT_SECRET: str
    DRIVE_TOKEN: str
    DRIVE_REFRESH_TOKEN: str


SCOPES = ["https://www.googleapis.com/auth/drive"]
DRIVE_TOKEN_TEMPLATE = {
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": SCOPES,
    "universe_domain": "googleapis.com",
    "account": "",
    "expiry": "2024-12-09T13:12:15.397414Z"
}
DRIVE_CREDENTIALS_TEMPLATE = {
    "auth_uri":"https://accounts.google.com/o/oauth2/auth",
    "token_uri":"https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris":["http://localhost"]
}


class CredentialsError(Exception):
    pass


class DriveCredentials:
    def __init__(self, config: DriveConfig):
        self.config = config
        token_dict = DRIVE_TOKEN_TEMPLATE.copy()
        token_dict.update({
            "token": config.DRIVE_TOKEN,
            "refresh_token": config.DRIVE_REFRESH_TOKEN,
            "client_id": config.DRIVE_CLIENT_ID,
            "client_secret": config.CLIENT_SECRET
        })
        self.token_dict = token_dict

    def get_drive_credentials(self) -> Credentials:
        creds = Credentials.from_authorized_user_info(self.token_dict, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise CredentialsError("Invalid DRIVE credentials")

            # Save the credentials for the next run
            self.token_dict = json.loads(creds.to_json())

        return creds


class SheetServiceFacade:
    def __init__(self, service):
        self.service = service

    def get(self, spreadsheet_id: str, range_: str) -> list[list[Any]]:
        result = (
            self.service.values()
            .get(spreadsheetId=spreadsheet_id, range=range_)
            .execute()
        )
        return result.get("values", [])

    def update(self, spreadsheet_id: str, range_: str, body: list[list[Any]]):
        return self.service.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            body={"values": body},
        ).execute()


class DriveFile(BaseModel):
    id: str
    name: str
    mimeType: str
    modifiedTime: str
    webViewLink: str


class FilesServiceFacade:
    def __init__(self, service):
        self.service = service

    def get_file(self, idx: str) -> DriveFile:
        result = self.service(
            pageSize=50,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
            q=f"id = '{idx}'"
            ).execute()
        file = result.get("files", [])[0]
        return DriveFile(**file)
    

class ServiceGenerator:
    def __init__(self, drive_creds: DriveCredentials):
        self.drive_creds = drive_creds

    def get_service(self, service_name: str, version: Literal["v4", "v3"]):
        creds = self.drive_creds.get_drive_credentials()
        return build(service_name, version, credentials=creds)
    
    def get_sheet_service(self) -> SheetServiceFacade:
        return SheetServiceFacade(self.get_service("sheets", "v4").spreadsheets())
    
    def get_files_service(self) -> FilesServiceFacade:
        return FilesServiceFacade(self.get_service("drive", "v3").files())


def get_service_generator(config: DriveConfig) -> ServiceGenerator:
    creds = DriveCredentials(config)
    return ServiceGenerator(creds)

def get_sheet_service(config: DriveConfig) -> SheetServiceFacade:
    service_generator = get_service_generator(config)
    return service_generator.get_sheet_service()

def get_files_service(config: DriveConfig) -> FilesServiceFacade:
    service_generator = get_service_generator(config)
    return service_generator.get_files_service()
