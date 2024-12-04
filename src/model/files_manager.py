import json
from typing import Protocol

from pydantic import BaseModel

from src.defaults import PROJECT_PATH


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
    source: SourceFile
    vector_store: VectorStoreFile


class FilesManagerI(Protocol):

    def get_file_link(self, idx: str) -> FileLink:
        ...


class InMemoryFilesManager:
    def __init__(self, files_dict: dict[str, FileLink]):
        self.files = files_dict

    def get_file_link(self, idx: str) -> FileLink | None:
        return self.files.get(idx, None)


def create_in_memory_files_manager() -> InMemoryFilesManager:
    with open(PROJECT_PATH / "file_links.json", "r") as f:
        files_dict = json.load(f)

    file_links_dict = {}
    for key, value in files_dict.items():
        file_links_dict[key] = FileLink(**value)
    files_manager = InMemoryFilesManager(file_links_dict)
    return files_manager
