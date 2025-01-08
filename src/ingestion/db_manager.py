from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from model.files.drive import DriveSheetManager
from utils.drive_utils import SheetServiceFacade


FileSources = Literal["drive", "gcs"]


FileStatus = Literal["ok", "updated", "deleted"]


class VectorStoreFileInfo(BaseModel):
    """Represents a file in the VectorStore database.
    Has information on both the OpenAI vector store file and 
    the source file in Google Drive/Google Cloud Storage."""
    
    id: str                  # OpenAI vector store file id
    source_id: str           # Google Drive file id
    source: FileSources      # Source of the file
    folder_id: str           # Container folder id
    last_modified: datetime  # Last modified time of the file
    status: FileStatus       # Status of the file in the VectorStore


class VectorStoreFilesDB(DriveSheetManager):

    def __init__(self, service: SheetServiceFacade, spreadsheet_id: str, 
                 sheet_name: str, vector_store_id: str) -> None:
        super().__init__(service, spreadsheet_id, sheet_name)
        self.vector_store_id = vector_store_id
    
    def write(self, file_info: VectorStoreFileInfo):
        next_row = self.next_row()
        self.write_row(next_row, [
            file_info.id, 
            file_info.source_id, 
            file_info.source, 
            file_info.folder_id, 
            str(file_info.last_modified),
            file_info.status])
    
    def get_ids_mapping(self) -> dict[str, str]:
        result = self.service.get(
            spreadsheet_id=self.spreadsheet_id, 
            range_=f"{self.sheet_name}!A2:F")
        
        return {r[0]: r[1] for r in result if r[5] == "ok"}
    
    def get_rows_dict(self) -> dict[str, int]:
        """Returns a dictionary mapping the source id to the row index in sheet."""
        result = self.service.get(
            spreadsheet_id=self.spreadsheet_id, 
            range_=f"{self.sheet_name}!A2:F")
        
        return {r[1]: i + 2 for i, r in enumerate(result) if r[5] == "ok"}
    
    def get_all(self) -> list[VectorStoreFileInfo]:
        result = self.service.get(
            spreadsheet_id=self.spreadsheet_id, 
            range_=f"{self.sheet_name}!A2:F")
        
        return [VectorStoreFileInfo(
            id=r[0], 
            source_id=r[1], 
            source=r[2], 
            folder_id=r[3], 
            last_modified=datetime.fromisoformat(r[4]),
            status=r[5]) for r in result if r[5] == "ok"]
    
    def update_status(self, source_id: str, status: FileStatus):
        rows_dict = self.get_rows_dict()
        row = rows_dict.get(source_id, None)

        current_entry = self.service.get(
            spreadsheet_id=self.spreadsheet_id, 
            range_=f"{self.sheet_name}!A:F{row}")
        
        assert current_entry[0][1] == source_id, "Mismatch in source id."
        assert current_entry[0][5] == "ok", "File status is not ok."

        if row is not None:
            self.service.update(
                spreadsheet_id=self.spreadsheet_id,
                range_=f"{self.sheet_name}!F{row}",
                body=[[status]])
