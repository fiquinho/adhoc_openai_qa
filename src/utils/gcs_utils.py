from typing import Protocol
from pydantic import BaseModel
from google.cloud import storage
from google.oauth2 import service_account

from model.files.gcs import GCSFile


class GCSConfig(BaseModel):
    PROJECT_ID: str
    PRIVATE_KEY_ID: str
    PRIVATE_KEY: str
    CLIENT_EMAIL: str
    CLIENT_ID: str
    CLIENT_X509_CERT_URL: str


GCS_JSON_TEMPLATE = {
    "type": "service_account",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "universe_domain": "googleapis.com"
}


class GCSClientGenerator:
    def __init__(self, config: GCSConfig):
        self.config = config
        gcs_json = GCS_JSON_TEMPLATE.copy()
        init_dict = {key.lower(): value for key, value in self.config.model_dump().items()}
        gcs_json.update(init_dict)
        self.gcs_json = gcs_json

    def get_client(self) -> storage.Client:
        return storage.Client(
            credentials=service_account.Credentials.from_service_account_info(
                self.gcs_json,
                scopes=['https://www.googleapis.com/auth/cloud-platform'],
            ),
        )


class SourcesManagerI(Protocol):
    
    def get_files(self, extensions: list[str]) -> list[GCSFile]:
        ...

    def download_as_bytes(self, file: GCSFile) -> bytes:
        ...
        

class GCSBucketFacade:

    def __init__(self, bucket: storage.Bucket):
        self.bucket = bucket

    def get_folder_files(self, folder: str, extensions: list[str]) -> list[GCSFile]:
        bucket_blobs = [GCSFile.from_blob(blob) for blob in 
                        self.bucket.list_blobs(prefix=folder)
                        if blob.content_type in extensions]
        return bucket_blobs

    def download_as_bytes(self, file: GCSFile) -> bytes:
        blob = self.bucket.blob(file.name)
        return blob.download_as_bytes()
    
    
def get_gcs_bucket(bucket_name: str, config: GCSConfig) -> GCSBucketFacade:
    client_generator = GCSClientGenerator(config)
    storage_client = client_generator.get_client()
    bucket = storage_client.get_bucket(bucket_name)
    return GCSBucketFacade(bucket)