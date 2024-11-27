from pathlib import Path
from unittest.mock import Mock

import pytest
from openai.types import FileObject

from src.files_manager import OpenAIFileManager


@pytest.fixture
def file_dict():
    return {
        "id": "123",
        "object": "file",
        "bytes": 1000,
        "created_at": 123456,
        "filename": "image.jpg",
        "purpose": "assistants",
        "status": "uploaded",
        'status_details': None
    }


def test_file(file_dict):

    file = FileObject(**file_dict)
    assert file.id == "123"
    assert file.object == "file"
    assert file.bytes == 1000
    assert file.created_at == 123456
    assert file.filename == "image.jpg"
    assert file.purpose == "assistants"
    assert file.status == "uploaded"
    assert file.status_details is None

    assert file.model_dump() == file_dict


def test_openai_file_manager(file_dict):
    client = Mock()
    client.files.list.return_value = [FileObject(**file_dict)]
    file_manager = OpenAIFileManager(client)

    assert file_manager.files_list() == [FileObject(**file_dict)]

    assert file_manager.add(file_path=Path("new_image.jpg"), purpose="assistants")
    assert not file_manager.add(file_path=Path("image.jpg"), purpose="assistants")

    client.files.create.assert_called_once_with(file=Path("new_image.jpg"), purpose="assistants")
