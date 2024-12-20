from pydantic import BaseModel
from googleapiclient.discovery import build

from src.utils.drive_utils import DriveCredentials, ServiceGenerator


DRIVE_MIMETYPES_DICT = {
    "application/vnd.google-apps.document": "docx",
    "application/vnd.google-apps.spreadsheet": "xlsx",
    "application/pdf": "pdf",
}

DRIVE_EXTENSION_TO_MIMETYPE = {value: key for key, value in DRIVE_MIMETYPES_DICT.items()}


class DriveFolder(BaseModel):
    id: str
    name: str
    mimeType: str
    webViewLink: str


class DriveFile(BaseModel):
    id: str
    name: str
    mimeType: str
    modifiedTime: str
    webViewLink: str


# TODO: Create only one service for sequential operations
class DriveSheetManager:
    def __init__(self, service_gen: ServiceGenerator, spreadsheet_id: str, sheet_name: str) -> None:
        self.service_gen = service_gen
        self.service = service_gen.get_sheet_service()
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
    
    def next_row(self) -> int:
        result = (
            self.service.values()
            .get(spreadsheetId=self.spreadsheet_id, range=f"{self.sheet_name}!A:A")
            .execute()
        )
        last_row = len(result.get("values", []))
        return last_row + 1
    
    def write_row(self, row_number: int, values: list[str | int | float | None]) -> None:
        body = {"values": [values]}

        self.service.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A{row_number}",
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()


class SourcesSheetManager(DriveSheetManager):

    def write(self, source_id: str):
        next_row = self.next_row()
        self.write_row(next_row, [source_id])
        


class NameCleaner:

    def __init__(self, types_dict: dict[str, str], delete: list[str], replace: str):
        self.types_dict = types_dict
        self.delete = delete
        self.replace = replace

    def clean_name(self, name: str, mime_type: str) -> str:
        for c in self.delete:
            name = name.replace(c, self.replace)

        extension = self.types_dict.get(mime_type, None)
        if extension is not None:
            name = name + '.' + extension

        return name


class DriveNameCleaner(NameCleaner):

    def __init__(self):
        super().__init__(types_dict=DRIVE_MIMETYPES_DICT,
                         delete=['/', ':', '?'],
                         replace='_')
