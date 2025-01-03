from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from model.files.drive import DriveSheetManager


FileSources = Literal["drive", "gcs"]


class VectorStoreFileInfo(BaseModel):
    """Represents a file in the VectorStore database.
    Has information on both the OpenAI vector store file and 
    the source file in Google Drive/Google Cloud Storage."""
    
    id: str                  # OpenAI vector store file id
    source_id: str           # Google Drive file id
    source: FileSources      # Source of the file
    folder_id: str           # Container folder id
    last_modified: datetime  # Last modified time of the file


class VectorStoreFilesDB(DriveSheetManager):

    def write(self, file_info: VectorStoreFileInfo):
        next_row = self.next_row()
        self.write_row(next_row, [
            file_info.id, 
            file_info.source_id, 
            file_info.source, 
            file_info.folder_id, 
            str(file_info.last_modified)])
        
    def get_sources(self) -> list[str]:
        result = self.service.get(
            spreadsheet_id=self.spreadsheet_id, 
            range_=f"{self.sheet_name}!B2:B")
        
        return [r[0] for r in result]
    
    def get_ids_mapping(self) -> dict[str, str]:
        result = self.service.get(
            spreadsheet_id=self.spreadsheet_id, 
            range_=f"{self.sheet_name}!A2:B")
        
        return {r[0]: r[1] for r in result}
