from hmac import new
import os
import streamlit as st

from src.model.files.drive import DriveFolder, SourcesSheetManager
from src.utils.dotenv_utils import load_config
from src.utils.drive_utils import DriveConfig, DriveCredentials, ServiceGenerator
from src.ingestion.sources import SUPPORTED_FILES, DriveSheetSourcesManager

if 'drive_credentials' not in st.session_state:
    drive_config: DriveConfig = load_config(DriveConfig, os.getenv)
    st.session_state.drive_credentials = DriveCredentials(drive_config)
if 'drive_service_gen' not in st.session_state:
    drive_credentials: DriveCredentials = st.session_state.drive_credentials
    st.session_state.drive_service_gen = ServiceGenerator(drive_credentials)
if "drive_sources_manager" not in st.session_state:
    creds = st.session_state.drive_credentials.get_drive_credentials()
    st.session_state.drive_sources_manager = DriveSheetSourcesManager(creds=creds, sheet_id="1XAhPXBsAecJUiyI13l6qtiI-iuITA4XjyDI11BLmGDo")
if 'new_source_info' not in st.session_state:
    st.session_state.new_source_info = None
if "sources_manager" not in st.session_state:
    drive_service_gen: ServiceGenerator = st.session_state.drive_service_gen
    st.session_state.sources_manager = SourcesSheetManager(drive_service_gen, 
                                                           "1XAhPXBsAecJUiyI13l6qtiI-iuITA4XjyDI11BLmGDo",
                                                           "Sources")


def get_new_source_info():
    new_source_id = st.session_state.new_source_id
    sources_manager: DriveSheetSourcesManager = st.session_state.drive_sources_manager
    
    new_source_info: DriveFolder | Exception
    try:
        new_source_info = sources_manager.get_folder(new_source_id)
    except Exception as e:
        new_source_info = e
    
    st.session_state.new_source_info = new_source_info


def add_new_source():
    new_source_id = st.session_state.new_source_id
    sources_manager: SourcesSheetManager = st.session_state.sources_manager
    sources_manager.write(new_source_id)
    


def main():
    st.text_input("New source folder ID", key="new_source_id", on_change=get_new_source_info)

    new_source_info = st.session_state.new_source_info
    if isinstance(new_source_info, DriveFolder):
        st.markdown(f"New source folder: {new_source_info.name}")
        st.markdown(f"[Link]({new_source_info.webViewLink})")
        if st.button("Add new source"):
            add_new_source()
    elif new_source_info is not None:
        st.error(f"Folder not found")
        st.text(new_source_info)

    st.markdown("---")

    selection = st.pills("Supported files", SUPPORTED_FILES, selection_mode="multi", 
                         default=SUPPORTED_FILES)
    
    sources_manager: DriveSheetSourcesManager = st.session_state.drive_sources_manager
    source_folders = sources_manager.get_sources_folders()
    
    for folder in source_folders:
        with st.expander(folder.name):
            st.markdown(f"[Link]({folder.webViewLink}) - ID: {folder.id}")
            files = sources_manager.get_folder_files(folder.id, selection)
            for file in files:
                st.markdown(f"[{file.name}](file.webViewLink) - Modified: {file.modifiedTime}")



if __name__ == "__main__":
    main()