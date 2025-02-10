from httpx import delete
from openai import OpenAI

from ingestion.db_manager import VectorStoreFileInfo, VectorStoreFilesDB
from model.files.gcs import GCSFile


class SourcesDifferences:
    """Represents the differences between the source files and the VectorStore files."""
    
    def __init__(self):
        self.new_files: list[GCSFile] = []
        self.updated: list[tuple[GCSFile, VectorStoreFileInfo]] = []
        self.deleted: list[VectorStoreFileInfo] = []
        self.no_changes: list[GCSFile] = []


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
            source_file_id=file.file_name,
            source_type="gcs",
            folder_id=file.file_folder,
            last_modified=file.updated,
            status="ok",
            source_id=file.file_folder + "/" + file.file_name
        )

        self.vs_files_db.write(file_info)
        self.openai_client.beta.vector_stores.files.create(
            vector_store_id=self.vs_files_db.vector_store_id,
            file_id=vs_file.id
        )
    
    def delete_file(self, file: VectorStoreFileInfo):
        self.openai_client.beta.vector_stores.files.delete(
            vector_store_id=self.vs_files_db.vector_store_id,
            file_id=file.id
        )
        self.openai_client.files.delete(file.id)
        self.vs_files_db.update_status(file.source_id, "deleted")

    def update_file(self, gcs_file: GCSFile, file_bytes: bytes, vs_file: VectorStoreFileInfo):
        self.openai_client.beta.vector_stores.files.delete(
            vector_store_id=self.vs_files_db.vector_store_id,
            file_id=vs_file.id
        )
        self.openai_client.files.delete(vs_file.id)
        self.vs_files_db.update_status(vs_file.source_id, "updated")
        self.ingest_file(gcs_file, file_bytes)
