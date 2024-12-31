from openai import OpenAI
import tqdm
from defaults import DEFAULT_ENV_FILE
from ingestion.db_manager import VectorStoreFilesDB
from ingestion.manager import IngestionManager
from model.answers_generation import OpenAIConfig
from utils.dotenv_utils import FromFileConfigGenerator, load_config
from utils.drive_utils import DriveConfig, get_sheet_service
from utils.gcs_utils import GCSConfig, get_gcs_bucket


def main():
    configs_getter = FromFileConfigGenerator(DEFAULT_ENV_FILE)

    gcs_config: GCSConfig = load_config(GCSConfig, configs_getter.get_config)
    openai_config: OpenAIConfig = load_config(OpenAIConfig, configs_getter.get_config)
    drive_config = load_config(DriveConfig, configs_getter.get_config)

    bucket = get_gcs_bucket('bucket-optimusprime', gcs_config)
    bucket_blobs = bucket.get_files(["application/pdf"])

    openai_client = OpenAI(api_key=openai_config.OPENAI_API_KEY, organization=openai_config.OPENAI_ORG_ID)

    sheet_service = get_sheet_service(drive_config)
    vs_files_db = VectorStoreFilesDB(sheet_service,
                                    "1XAhPXBsAecJUiyI13l6qtiI-iuITA4XjyDI11BLmGDo",
                                    "VectorStore")
    sources_ids = vs_files_db.get_sources()
    
    ingestion_manger = IngestionManager(openai_client, vs_files_db)

    for blob in tqdm.tqdm(bucket_blobs):
        if blob.file_name in sources_ids:
            continue

        try:
            file_bytes = bucket.download_as_bytes(blob)
            ingestion_manger.ingest_file(blob, file_bytes)
        except Exception as e:
            print(f"Error ingesting file {blob.file_name}: {e}")
        
        


if __name__ == "__main__":
    main()
