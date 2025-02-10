import pytest
from pydantic import BaseModel

from src.utils.config_utils import DotEnvConfigGenerator, load_environment_config


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


class Config(BaseModel):
    USER: str
    ID: int
    ADMIN: bool
    PROD: bool
    OPTIONAL: str | None = None


def test_from_file_config_generator(test_env_file):
    config = DotEnvConfigGenerator(test_env_file)
    assert config._config_dict == {
        "USER": "test_user",
        "ID": "123",
        "ADMIN": "True",
        "PROD": "False"
    }

    assert config.getenv("USER") == "test_user"
    assert config.getenv("ID") == "123"
    assert config.getenv("ADMIN") == "True"
    assert config.getenv("PROD") == "False"
    assert config.getenv("NOT_EXIST") is None


def test_load_config():
    config = load_environment_config(Config, GetValueSpy())

    assert config.USER == "test_user"
    assert config.ID == 123
    assert config.ADMIN is True
    assert config.PROD is False
    assert config.OPTIONAL is None


class GetValueSpy:
    def __init__(self):
        self.value = {
            "USER": "test_user",
            "ID": "123",
            "ADMIN": "True",
            "PROD": "False"
        }

    def __call__(self, key):
        return self.value.get(key)
