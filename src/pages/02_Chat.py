from copy import deepcopy
import os
from time import sleep
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel
import streamlit as st

from model.answers_generation import MarkdownAnswer, OpenAIConfig, QuestionsAnswers, QuestionsAnswersI, QuestionsAnswersMock
from defaults import DEFAULT_CONFIG_FILE, OPTIMUS_IMAGE
from ingestion.db_manager import VectorStoreFilesDB
from model.files_manager import FileLink, InMemoryFilesManager, SheetFilesDB
from utils.streamlit_utils import AppConfig
from utils.drive_utils import DriveConfig, get_sheet_service
from utils.config_utils import load_environment_config, load_toml_config
from model.feedback.feedback import TestLog, SheetLogWriter, YesNoPartially


openai_config: OpenAIConfig = load_environment_config(OpenAIConfig, os.getenv)
drive_config: DriveConfig = load_environment_config(DriveConfig, os.getenv)



class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str | MarkdownAnswer


TEST_CONVERSATION = [
        ChatMessage(role="assistant", content="Hola, soy Optimus, en qué puedo ayudarte?")
    ]


FilesManagersDict = dict[str, SheetFilesDB]


if "app_config" not in st.session_state:
    st.session_state.app_config = load_toml_config(AppConfig, DEFAULT_CONFIG_FILE)

if "conversation" not in st.session_state:
    st.session_state.conversation = deepcopy(TEST_CONVERSATION)
if 'answer_model' not in st.session_state:
    _app_config: AppConfig = st.session_state.app_config
    openai_client = OpenAI(api_key=openai_config.OPENAI_API_KEY, organization=openai_config.OPENAI_ORG_ID)
    st.session_state.answer_model = QuestionsAnswers(openai_client, _app_config.assistant.id)

if 'files_managers' not in st.session_state:
    _app_config: AppConfig = st.session_state.app_config
    sheet_service = get_sheet_service(drive_config)
    files_managers: FilesManagersDict = {}
    for data_version in _app_config.vector_stores.data_versions:
        vs = VectorStoreFilesDB(
            sheet_service,
            _app_config.vector_stores.spreadsheet_id,
            data_version.sheet_name,
            data_version.vector_store_id)
        files_managers[data_version.version] = SheetFilesDB(vs)
    st.session_state.files_managers = files_managers

    # st.session_state.files_manager = InMemoryFilesManager({
    #     "mock_file_1": FileLink(name="Google", url="https://www.google.com"),
    #     "mock_file_2": FileLink(name="X", url="https://www.x.com")
    # })


def reset_chat():
    st.session_state.conversation = deepcopy(TEST_CONVERSATION)


def submit_message():
    with st.spinner("Thinking..."):
        
        message = st.session_state.message
        conversation: list[ChatMessage] = st.session_state.conversation
        
        conversation.append(ChatMessage(role="user", content=message))

        version: str = st.session_state.chat_version
        files_managers: FilesManagersDict = st.session_state.files_managers
        vector_store_id: str = files_managers[version].files_db.vector_store_id

        answer_model: QuestionsAnswersI = st.session_state.answer_model
        answer = answer_model.answer(message, vector_store_id)

        markdown_answer = MarkdownAnswer.from_llm_answer(answer, files_managers[version])
        conversation.append(ChatMessage(role="assistant", content=markdown_answer))


def main():

    files_managers: FilesManagersDict = st.session_state.files_managers
    versions = list(files_managers.keys())
    st.selectbox("Version", options=versions, key="chat_version")

    conversation: list[ChatMessage] = st.session_state.conversation
    if len(conversation) >= 1:
        for message in conversation:
            if message.role == "assistant":
                if isinstance(message.content, MarkdownAnswer):
                    with st.chat_message("assistant", avatar=str(OPTIMUS_IMAGE)):
                        st.markdown(message.content.text)
                        st.markdown("#### Referencias")
                        for reference in message.content.references:
                            st.markdown(reference)
                        
                        # with st.form("form"):
                        #     was_solved: YesNoPartially = st.radio("Resolvió tu duda?", options=YesNoPartially.__args__, key="was_solved")
                        #     was_detailed: YesNoPartially = st.radio("La respuesta fue detallada?", options=YesNoPartially.__args__, key="was_detailed")
                        #     note = st.text_area("Sugerencia", key="note")

                        #     test_log = "TestLog"

                        #     if st.form_submit_button("Submit"):
                        #         print(test_log)
                        #         print("Submitted")

                else:
                    with st.chat_message("assistant", avatar=str(OPTIMUS_IMAGE)):
                        st.write(message.content)
            else:
                with st.chat_message("user"):
                    st.write(message.content)

    
    st.chat_input("Say something", key="message", on_submit=submit_message)

    st.button("Reset chat", on_click=reset_chat)

if __name__ == '__main__':
    main()
