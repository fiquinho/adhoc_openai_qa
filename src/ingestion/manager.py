from openai import OpenAI

from ingestion.db_manager import VectorStoreFileInfo, VectorStoreFilesDB
from model.files.gcs import GCSFile


class IngestionManager:
    def __init__(self, openai_client: OpenAI, vs_files_db: VectorStoreFilesDB):
        self.openai_client = openai_client
        self.vs_files_db = vs_files_db

    def ingest_file(self, file: GCSFile, file_bytes: bytes):
        vs_file = self.openai_client.files.create(
            file=(file.full_file_name, file_bytes),
            purpose="assistants"
        )

        file_info = VectorStoreFileInfo(
            id=vs_file.id,
            source_id=file.file_name,
            source="gcs",
            folder_id=file.file_folder,
            last_modified=file.updated
        )
        self.vs_files_db.write(file_info)