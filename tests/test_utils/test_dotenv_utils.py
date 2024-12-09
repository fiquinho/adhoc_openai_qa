import pytest
from pydantic import BaseModel

from src.utils.dotenv_utils import config_from_file


@pytest.fixture
def test_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "USER=test_user\n"
        "ID=123\n"
        "ADMIN=True\n"
        "PROD=False\n"
    )
    return env_file


class TestConfig(BaseModel):
    USER: str
    ID: int
    ADMIN: bool
    PROD: bool


def test_config_from_file(test_env_file):
    config: TestConfig = config_from_file(test_env_file, TestConfig)

    assert config.USER == "test_user"
    assert config.ID == 123
    assert config.ADMIN is True
    assert config.PROD is False
