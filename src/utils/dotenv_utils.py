from pathlib import Path
from typing import Type, TypeVar, Callable

from pydantic import BaseModel
from dotenv import dotenv_values
from pydantic.fields import FieldInfo


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
    init_args = {}
    # noinspection PyUnresolvedReferences
    for field in dataclass.model_fields.items():
        field_name: str = field[0]
        field_info: FieldInfo = field[1]

        value = get_value_fn(field_name)
        if value is None:
            init_args[field_name] = value
            continue

        # Special case for bool fields
        if field_info.annotation is bool:
            value = value.lower() in ['true', '1']
        
        if field_info.annotation is None:
            raise ValueError(f"Field {field_name} has no annotation")
        init_args[field_name] = field_info.annotation(value)

    return dataclass(**init_args)
