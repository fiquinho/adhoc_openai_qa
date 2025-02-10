from datetime import datetime
import os
import tomli
import json
from openai import OpenAI
import streamlit as st
import pandas as pd
from tqdm import tqdm

from ingestion.db_manager import VectorStoreFileInfo, VectorStoreFilesDB
from model.files_manager import SheetFilesDB
from model.files.gcs import GCSFile
from model.answers_generation import OpenAIConfig
from ingestion.manager import IngestionManager, SourcesDifferences
from ingestion.config import VectorStoreConfig
from defaults import DEV_CONFIG_FILE, DEFAULT_CONFIG_FILE
from utils.config_utils import load_environment_config
from utils.drive_utils import DriveConfig, get_sheet_service
from utils.gcs_utils import GCSBucketFacade, GCSConfig, get_gcs_bucket


drive_config: DriveConfig = load_environment_config(DriveConfig, os.getenv)
gcs_config: GCSConfig = load_environment_config(GCSConfig, os.getenv)
openai_config: OpenAIConfig = load_environment_config(OpenAIConfig, os.getenv)
openai_client = OpenAI(api_key=openai_config.OPENAI_API_KEY, organization=openai_config.OPENAI_ORG_ID)


# with open(DEV_CONFIG_FILE, mode="rb") as fp:
#     config = tomli.load(fp)

with open(DEFAULT_CONFIG_FILE, mode="rb") as fp:
    config = tomli.load(fp)

vector_store_config = VectorStoreConfig(**config["vector_stores"])


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


VectorStoresDict = dict[str, VectorStoreFilesDB]
DifferencesDict = dict[str, SourcesDifferences]


if 'vs_files_db_dict' not in st.session_state:
    sheet_service = get_sheet_service(drive_config)
    vs_files_db_dict: VectorStoresDict = {}
    for data_version in vector_store_config.data_versions:
        vs_files_db_dict[data_version.bucket_folder] = VectorStoreFilesDB(
            sheet_service,
            vector_store_config.spreadsheet_id,
            data_version.sheet_name,
            data_version.vector_store_id)
    st.session_state.vs_files_db_dict = vs_files_db_dict

if "bucket" not in st.session_state:
    st.session_state.bucket = get_gcs_bucket(vector_store_config.bucket_name, gcs_config)

if 'diffs_dict' not in st.session_state:
    st.session_state.diffs_dict = None


def sync_files():
    sources_differences_dict: DifferencesDict = st.session_state.diffs_dict
    vs_files_db_dict: VectorStoresDict = st.session_state.vs_files_db_dict
    bucket: GCSBucketFacade = st.session_state.bucket

    for bucket_folder, sources_differences in sources_differences_dict.items():
        files_db = vs_files_db_dict[bucket_folder]
        ingestion_manager = IngestionManager(openai_client, files_db)

        print(f"Syncing files for data version: {bucket_folder}")

        print(f"New files: {len(sources_differences.new_files)}")
        for file in tqdm(sources_differences.new_files):
            file_bytes = bucket.download_as_bytes(file)
            ingestion_manager.ingest_file(file, file_bytes)
        
        print(f"Deleted files: {len(sources_differences.deleted)}")
        for file in tqdm(sources_differences.deleted):
            ingestion_manager.delete_file(file)

        print(f"Updated files: {len(sources_differences.updated)}")
        for file_blob, file_vs in tqdm(sources_differences.updated):
            file_bytes = bucket.download_as_bytes(file_blob)
            ingestion_manager.update_file(file_blob, file_bytes, file_vs)


def main():
    st.markdown("# Sync source files")
    vs_files_db_dict: VectorStoresDict = st.session_state.vs_files_db_dict

    diffs_dict: DifferencesDict = {}
    for bucket_folder, vs_files_db in vs_files_db_dict.items():
        st.markdown(f"# Data version: {bucket_folder}")

        files = vs_files_db.get_all()
        
        vs_files_df = pd.DataFrame([file.model_dump() for file in files])
        vs_files_indexs = set(range(len(files)))

        st.markdown("### Files in VectorStore")
        st.markdown(f"DataBase URL: [optimus_openai_files_system]"
                    f"(https://docs.google.com/spreadsheets/d/{vector_store_config.spreadsheet_id})")
        st.markdown(f"Sheet: '{vs_files_db.sheet_name}'")
        with st.expander("Explore"):
            st.dataframe(vs_files_df)
        st.markdown(f"Total files: {len(files)}")

        bucket: GCSBucketFacade = st.session_state.bucket
        bucket_blobs = bucket.get_folder_files(bucket_folder, ["application/pdf"])
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
                row = vs_files_df.index[vs_files_df['source_id'] == blob.source_id]
                if row.empty:
                    sources_differences.new_files.append(blob)
                else:
                    vs_file_index = int(row[0])
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
                st.write(file.source_id)

        with st.expander(f"Updated files ({len(sources_differences.updated)})"):
            for file in sources_differences.updated:
                st.write(file[0].source_id)
        
        with st.expander(f"Deleted files ({len(sources_differences.deleted)})"):
            for file in sources_differences.deleted:
                st.write(file.source_id)
        
        with st.expander(f"No changes files ({len(sources_differences.no_changes)})"):
            for file in sources_differences.no_changes:
                st.write(file.source_id)
        
        diffs_dict[bucket_folder] = sources_differences

    st.session_state.diffs_dict = diffs_dict
    st.button("Sync files", on_click=sync_files)


if __name__ == '__main__':
    main()