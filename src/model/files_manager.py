import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from ingestion.db_manager import VectorStoreFilesDB


class VectorStoreFile(BaseModel):
    id: str
    bytes: int
    filename: str


class SourceFile(BaseModel):
    id: str
    name: str
    url: str
    thumbnail: str


class FileLink(BaseModel):
    name: str
    url: str


class FilesManagerI(Protocol):

    def get_file_link(self, idx: str) -> FileLink: ...


class InMemoryFilesManager:
    def __init__(self, files_dict: dict[str, FileLink]):
        self.files = files_dict

    def get_file_link(self, idx: str) -> FileLink | None:
        return self.files.get(idx, None)


def in_memory_files_manager_from_json(file: Path) -> InMemoryFilesManager:
    with open(file, "r") as f:
        files_dict = json.load(f)

    file_links_dict = {}
    for key, value in files_dict.items():
        file_links_dict[key] = FileLink(name=value["source"]["name"],
                                        url=value["source"]["url"])
    files_manager = InMemoryFilesManager(file_links_dict)
    return files_manager


class SheetFilesDB:
    def __init__(self, files_db: VectorStoreFilesDB):
        self.files_db = files_db

    def get_file_link(self, idx: str) -> FileLink:
        files_dict = self.files_db.get_ids_mapping()
        file = files_dict.get(idx, None)
        if file is None:
            return FileLink(name="File not found", url="")
        return FileLink(name=file, url=f"https://docs.google.com/document/d/{file}")
