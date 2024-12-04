from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel
from dotenv import dotenv_values
# noinspection PyProtectedMember
from pydantic.fields import FieldInfo


BaseModelInstance = TypeVar('BaseModelInstance', bound=BaseModel)


def config_from_env(file_path: Path, dataclass: Type[BaseModel]) -> BaseModelInstance:
    """Load configuration from .env file and return a pydantic class instance"""
    env = dotenv_values(file_path)
    init_args = {}
    # noinspection PyUnresolvedReferences
    for field in dataclass.model_fields.items():
        field_name: str = field[0]
        field_info: FieldInfo = field[1]

        value = env.get(field_name)

        # Special case for bool fields
        if field_info.annotation is bool:
            value = value.lower() in ['true', '1']
        init_args[field_name] = field_info.annotation(value)

    return dataclass(**init_args)
