from pydantic import BaseModel

from model.feedback.feedback import FeedbackLogsConfig


class DataVersion(BaseModel):
    version: str
    sheet_name: str
    bucket_folder: str
    vector_store_id: str


class VectorStoreConfig(BaseModel):
    spreadsheet_id: str
    bucket_name: str
    data_versions: list[DataVersion]


class AssistantConfig(BaseModel):
    id: str


class AppConfig(BaseModel):
    vector_stores: VectorStoreConfig
    assistant: AssistantConfig
    feedback_logs: FeedbackLogsConfig
