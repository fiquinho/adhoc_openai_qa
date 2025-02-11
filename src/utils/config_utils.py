from pathlib import Path
from typing import Any, Type, TypeVar, Callable

import tomli
from pydantic import BaseModel
from dotenv import dotenv_values


# Generic type for a BaseModel instance
BaseModelInstance = TypeVar('BaseModelInstance', bound=BaseModel)


# Type for a function that gets a config value from its key
GetConfigValue = Callable[[str], str | None]


class DotEnvConfigGenerator:
    """
    Class to load a configuration from a .env file.
    Uses the python-dotenv library to load the configuration values.
    
    Attributes:
        file_path (Path): Path to the .env file
        _config_dict (dict): Dictionary with the configuration values
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._config_dict = self._load_config()

    def _load_config(self) -> dict[str, str | None]:
        """Loads the configuration from the .env file
        Returns:
            dict: Dictionary with the configuration values
        """
        return dotenv_values(self.file_path)

    def getenv(self, key: str) -> str | None:
        """Get a configuration value from its key.
        Args:
            key (str): The key of the configuration value
        Returns:
            str | None: The configuration value or None if not found
        """
        return self._config_dict.get(key)


def load_environment_config(
        dataclass: Type[BaseModelInstance], 
        getenv_fn: GetConfigValue
        ) -> BaseModelInstance:
    
    init_args: dict[str, Any] = {}

    for field_name, field_info in dataclass.model_fields.items():

        value = getenv_fn(field_name)
        if value is None:
            init_args[field_name] = value
            continue

        # Special case for bool fields
        if field_info.annotation is bool:
            bool_value = value.lower() in ['true', '1']
            init_args[field_name] = bool_value
            continue
        
        if field_info.annotation is not None:
            init_args[field_name] = field_info.annotation(value)

    return dataclass(**init_args)


def read_toml_file(file_path: Path) -> dict[str, Any]:

    if file_path.suffix != ".toml":
        raise ValueError("File must be a TOML file")
    
    with open(file_path, mode="rb") as fp:
        return tomli.load(fp)


def load_toml_config(
        dataclass: Type[BaseModelInstance], 
        file_path: Path
        ) -> BaseModelInstance:
    
    init_dict = read_toml_file(file_path)
    return dataclass(**init_dict)
