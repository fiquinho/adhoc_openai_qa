from datetime import datetime
from pydantic import BaseModel
from google.cloud.storage import Blob


GCS_TYPES = {
    "application/pdf": "pdf",
    "application/txt": "txt"
}

EXTENSION_TO_GCS_TYPE = {value: key for key, value in GCS_TYPES.items()}


class GCSFile(BaseModel):
    id: str
    name: str
    content_type: str
    updated: datetime

    @classmethod
    def from_blob(cls, blob: Blob) -> 'GCSFile':
        return cls(
            id=blob.id,                         # type: ignore
            name=blob.name,                     # type: ignore
            content_type=blob.content_type,
            updated=blob.updated,               # type: ignore
        )
    
    @property
    def full_file_name(self) -> str:
        return self.name.split('/')[-1]

    @property
    def file_folder(self) -> str:
        return "/".join(self.id.split('/')[:-2])
    
    @property
    def file_name(self) -> str:
        extension_length = len(GCS_TYPES[self.content_type]) + 1
        return self.full_file_name[:-extension_length]
    
    @property
    def source_id(self) -> str:
        return f"{self.file_folder}/{self.file_name}"
        
