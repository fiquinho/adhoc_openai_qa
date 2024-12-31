from datetime import datetime
from pydantic import BaseModel
from google.cloud.storage import Blob


GCS_TYPES = {
    "application/pdf": "pdf"
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
    def file_name(self) -> str:
        return self.name.split('/')[-1]

    @property
    def file_folder(self) -> str:
        return "/".join(self.id.split('/')[:-2])
    
    @property
    def full_file_name(self) -> str:
        return self.file_name + "." + GCS_TYPES[self.content_type]
