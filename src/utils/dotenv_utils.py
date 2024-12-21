from pathlib import Path
from typing import Any, Type, TypeVar, Callable

from pydantic import BaseModel
from dotenv import dotenv_values


BaseModelInstance = TypeVar('BaseModelInstance', bound=BaseModel)


GetConfigValue = Callable[[str], str | None]


class FromFileConfigGenerator:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._config_dict = self._load_config()

    def _load_config(self):
        return dotenv_values(self.file_path)

    def get_config(self, key: str) -> str | None:
        return self._config_dict.get(key)


def load_config(dataclass: Type[BaseModelInstance], get_value_fn: GetConfigValue) -> BaseModelInstance:
    init_args: dict[str, Any] = {}

    for field_name, field_info in dataclass.model_fields.items():
        
        if field_info.annotation is None:
            raise ValueError(f"Field {field_name} has no annotation")

        value = get_value_fn(field_name)
        if value is None:
            init_args[field_name] = value
            continue

        # Special case for bool fields
        if field_info.annotation is bool:
            bool_value = value.lower() in ['true', '1']
            init_args[field_name] = bool_value
            continue
        
        init_args[field_name] = field_info.annotation(value)

    return dataclass(**init_args)
