from datetime import datetime
import os
from openai import OpenAI
import streamlit as st
import pandas as pd

from ingestion.db_manager import VectorStoreFileInfo, VectorStoreFilesDB
from model import files_manager
from model.files_manager import SheetFilesDB
from model.files.gcs import GCSFile
from model.answers_generation import OpenAIConfig
from ingestion.manager import IngestionManager, SourcesDifferences
from utils.dotenv_utils import load_config
from utils.drive_utils import DriveConfig, get_sheet_service
from utils.gcs_utils import GCSBucketFacade, GCSConfig, get_gcs_bucket


drive_config: DriveConfig = load_config(DriveConfig, os.getenv)
gcs_config: GCSConfig = load_config(GCSConfig, os.getenv)
openai_config: OpenAIConfig = load_config(OpenAIConfig, os.getenv)
openai_client = OpenAI(api_key=openai_config.OPENAI_API_KEY, organization=openai_config.OPENAI_ORG_ID)


st.set_page_config(layout="wide")


dev_files_bytes: dict[str, bytes] = {
    "file1.txt": b"file1\nLorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "file2.txt": b"file2\nLorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "file3.txt": b"file3\nLorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "file4.txt": b"file4\nLorem ipsum dolor sit amet, consectetur adipiscing elit."
}


dev_bucket = [
    GCSFile(
        id="1",
        name="file1.txt",
        content_type="application/txt",
        updated=datetime.fromisoformat("2024-12-21 00:00:00+00:00")
    ),
    GCSFile(
        id="2",
        name="file2.txt",
        content_type="application/txt",
        updated=datetime.fromisoformat("2024-12-23 00:00:00+00:00")
    ),
    # GCSFile(
    #     id="3",
    #     name="file3.txt",
    #     content_type="application/txt",
    #     updated=datetime.fromisoformat("2024-12-21 00:00:00+00:00")
    # ),
    GCSFile(
        id="4",
        name="file4.txt",
        content_type="application/txt",
        updated=datetime.fromisoformat("2024-12-21 00:00:00+00:00")
    ),
]

DB_SPREADSHEET_ID = "1XAhPXBsAecJUiyI13l6qtiI-iuITA4XjyDI11BLmGDo"
DB_SHEET_NAME = "VectorStore"


if 'files_manager' not in st.session_state:
    sheet_service = get_sheet_service(drive_config)
    vs_files_db = VectorStoreFilesDB(sheet_service,
                                    DB_SPREADSHEET_ID,
                                    DB_SHEET_NAME,
                                    openai_config.VECTOR_STORE_ID)
    st.session_state.files_manager = SheetFilesDB(vs_files_db)

if "bucket" not in st.session_state:
    st.session_state.bucket = get_gcs_bucket('bucket-optimusprime', gcs_config)

if 'diffs' not in st.session_state:
    st.session_state.diffs = None


def sync_files():
    sources_differences: SourcesDifferences = st.session_state.diffs
    files_db: VectorStoreFilesDB = st.session_state.files_manager.files_db
    bucket: GCSBucketFacade = st.session_state.bucket

    ingestion_manager = IngestionManager(openai_client, files_db)

    for file in sources_differences.new_files:
        file_bytes = bucket.download_as_bytes(file)
        ingestion_manager.ingest_file(file, file_bytes)
    
    for file in sources_differences.deleted:
        ingestion_manager.delete_file(file)

    for file_blob, file_vs in sources_differences.updated:
        file_bytes = bucket.download_as_bytes(file_blob)
        ingestion_manager.update_file(file_blob, file_bytes, file_vs)


def main():
    files_manager: SheetFilesDB = st.session_state.files_manager
    files = files_manager.files_db.get_all()
    
    vs_files_df = pd.DataFrame([file.model_dump() for file in files])
    vs_files_indexs = set(range(len(files)))

    st.markdown("# Sync source files")
    st.markdown("### Files in VectorStore")
    st.markdown(f"DataBase URL: [optimus_openai_files_system]"
                f"(https://docs.google.com/spreadsheets/d/{DB_SPREADSHEET_ID})")
    st.markdown(f"Sheet: '{DB_SHEET_NAME}'")
    with st.expander("Explore"):
        st.dataframe(vs_files_df)
    st.markdown(f"Total files: {len(files)}")

    bucket: GCSBucketFacade = st.session_state.bucket
    bucket_blobs = bucket.get_files(["application/pdf"])
    # bucket_blobs = dev_bucket
    bucket_df = pd.DataFrame([file.model_dump() for file in bucket_blobs])

    st.markdown("### Files in Google Cloud Storage")
    st.markdown(f"Bucket: 'bucket-optimusprime'")
    with st.expander("Explore"):
        st.dataframe(bucket_df)
    st.markdown(f"Total files: {len(bucket_blobs)}")

    sources_differences = SourcesDifferences()

    if len(files) == 0:
        sources_differences.new_files = bucket_blobs

    else:
        for blob in bucket_blobs:
            row = vs_files_df.index[vs_files_df['source_id'] == blob.file_name]
            if row.empty:
                sources_differences.new_files.append(blob)
            else:
                vs_file_index = row[0]
                vs_files_indexs.remove(vs_file_index)
                vs_file: VectorStoreFileInfo = files[vs_file_index]
                if vs_file.last_modified < blob.updated:
                    sources_differences.updated.append((blob, vs_file))
                else:
                    sources_differences.no_changes.append(blob)
    
    for idx in vs_files_indexs:
        sources_differences.deleted.append(files[idx])
    
    st.markdown("### Differences")

    with st.expander(f"New files ({len(sources_differences.new_files)})"):
        for file in sources_differences.new_files:
            st.write(file.full_file_name)

    with st.expander(f"Updated files ({len(sources_differences.updated)})"):
        for file in sources_differences.updated:
            st.write(file[0].full_file_name)
    
    with st.expander(f"Deleted files ({len(sources_differences.deleted)})"):
        for file in sources_differences.deleted:
            st.write(file.source_id)
    
    with st.expander(f"No changes files ({len(sources_differences.no_changes)})"):
        for file in sources_differences.no_changes:
            st.write(file.full_file_name)
    
    st.session_state.diffs = sources_differences
    st.button("Sync files", on_click=sync_files)


if __name__ == '__main__':
    main()