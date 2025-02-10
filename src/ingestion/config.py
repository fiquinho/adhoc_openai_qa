import tomli
from pydantic import BaseModel

from defaults import DEV_CONFIG_FILE


with open(DEV_CONFIG_FILE, mode="rb") as fp:
    config = tomli.load(fp)
print(config)


class DataVersion(BaseModel):
    version: str
    sheet_name: str
    bucket_folder: str
    vector_store_id: str


class VectorStoreConfig(BaseModel):
    spreadsheet_id: str
    bucket_name: str
    data_versions: list[DataVersion]


