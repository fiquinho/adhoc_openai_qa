from pydantic import BaseModel

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource

from src.model.files.drive import DRIVE_EXTENSION_TO_MIMETYPE, DriveFile, DriveFolder


SUPPORTED_FILES = ["pdf", "docx"]


def generate_file_type_filter(supported_files: list[str]) -> str:
    filter = " or ".join([f"mimeType='{DRIVE_EXTENSION_TO_MIMETYPE[file]}'" for file in supported_files])
    return filter


class DriveSheetSourcesManager:

    def __init__(self, creds: Credentials, sheet_id: str):
        self.creds = creds
        self.sheet_id = sheet_id
        self.sheet_service = build("sheets", "v4", credentials=self.creds).spreadsheets()
        self.drive_service = build("drive", "v3", credentials=self.creds)

    def get_folder(self, folder_id: str) -> DriveFolder:
        folder = self.drive_service.files().get(fileId=folder_id, fields="id, name, mimeType, webViewLink").execute()
        return DriveFolder(**folder)

    def get_sources_folders(self) -> list[DriveFolder]:
        result = self.sheet_service.values().get(spreadsheetId=self.sheet_id, range="Sources!A2:A").execute()
        values = result.get('values', [])
        ids = [v[0] for v in values]

        folders = [self.get_folder(folder_id) for folder_id in ids]
        return folders

    def get_folder_files(self, folder_id: str, supported_types: list[str]) -> list[DriveFile]:
        filter = generate_file_type_filter(supported_types)
        results = self.drive_service.files().list(q=f"'{folder_id}' in parents and ({filter})",
                                                  fields="files(id, name, mimeType, modifiedTime, webViewLink)").execute()
        return [DriveFile(**v) for v in results.get('files', [])]