from dataclasses import dataclass

from pydantic import BaseModel

from src.utils.dotenv_utils import config_from_env
from tests.defaults import TESTS_PATH


TEST_ENV_FILE = TESTS_PATH / "test_utils" / ".env.test"


class TestConfig(BaseModel):
    USER: str
    ID: int
    ADMIN: bool
    PROD: bool


def test_config_from_env():

    config: TestConfig = config_from_env(TEST_ENV_FILE, TestConfig)

    assert config.USER == "test_user"
    assert config.ID == 123
    assert config.ADMIN is True
    assert config.PROD is False
