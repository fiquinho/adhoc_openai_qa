from unittest.mock import DEFAULT
import pytest
from pydantic import BaseModel

from src.utils.config_utils import DotEnvConfigGenerator, load_environment_config, read_toml_file, load_toml_config


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


def test_dotenv_config_generator(test_env_file):
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


def test_load_environment_config():
    config = load_environment_config(Config, GetValueSpy())

    assert config.USER == "test_user"
    assert config.ID == 123
    assert config.ADMIN is True
    assert config.PROD is False
    assert config.OPTIONAL is None


@pytest.fixture
def test_toml_file(tmp_path):
    toml_file = tmp_path / "config.toml"
    toml_file.write_text(
        "[DEFAULT]\n"
        "USER = 'test_user'\n"
        "ID = 123\n"
        "ADMIN = true\n"
        "PROD = false\n"
    )
    return toml_file


def test_read_toml_file(test_toml_file):
    config = read_toml_file(test_toml_file)
    assert config == {
        "DEFAULT": {
            "USER": "test_user",
            "ID": 123,
            "ADMIN": True,
            "PROD": False
        }
    }


def test_read_toml_file_error(tmp_path):
    with pytest.raises(ValueError):
        read_toml_file(tmp_path / "config.txt")


class TomlConfig(BaseModel):
    DEFAULT: Config


def test_load_toml_config(test_toml_file):
    config = load_toml_config(TomlConfig, test_toml_file)
    assert config.DEFAULT.USER == "test_user"
    assert config.DEFAULT.ID == 123
    assert config.DEFAULT.ADMIN is True
    assert config.DEFAULT.PROD is False
    assert config.DEFAULT.OPTIONAL is None
    

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
