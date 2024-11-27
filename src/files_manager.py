from pathlib import Path
from typing import Protocol, Literal

from openai import OpenAI
from openai.types import FileObject


Purpose = Literal["assistants", "vision", "batch", "fine-tune"]


class FilesManagerI(Protocol):

    def files_list(self) -> list[FileObject]:
        ...

    def add(self, file_path: Path, purpose: Purpose) -> bool:
        ...


class OpenAIFileManager:

    def __init__(self, client: OpenAI):
        self.client = client

    def add(self, file_path: Path, purpose: Purpose) -> bool:
        files_list = self.files_list()
        if any(file.filename == file_path.name for file in files_list):
            return False

        self.client.files.create(
            file=file_path,
            purpose=purpose
        )
        return True

    def files_list(self) -> list[FileObject]:
        return self.client.files.list()
