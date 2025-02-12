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
    """Loads environment configurations into a dataclass instance.
    Args:
        dataclass (Type[BaseModelInstance]): The dataclass type to instantiate.
        getenv_fn (GetConfigValue): A function that retrieves the environment variable value for a given field name.
    Returns:
        BaseModelInstance: An instance of the dataclass populated with values from the environment variables.
    Notes:
        - If an environment variable is not found for a field, the field is set to None.
        - Special handling is provided for boolean fields, where 'true' and '1' (case insensitive) are interpreted as True.
        - The function attempts to cast the environment variable value to the type specified in the dataclass field annotation.
    """

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
    """Reads a TOML file and returns its content as a dictionary.
    Args:
        file_path (Path): Path to the TOML file
    Returns:
        dict: Dictionary with the content of the TOML file
    Raises:
        ValueError: If the file is not a TOML file
    """

    if file_path.suffix != ".toml":
        raise ValueError("File must be a TOML file")
    
    with open(file_path, mode="rb") as fp:
        return tomli.load(fp)


def load_toml_config(
        dataclass: Type[BaseModelInstance], 
        file_path: Path
        ) -> BaseModelInstance:
    """Loads TOML configurations into a dataclass instance.
    Args:
        dataclass (Type[BaseModelInstance]): The dataclass type to instantiate.
        file_path (Path): Path to the TOML file.
    Returns:
        BaseModelInstance: An instance of the dataclass populated with values from the TOML file.
    """
    init_dict = read_toml_file(file_path)
    return dataclass(**init_dict)
