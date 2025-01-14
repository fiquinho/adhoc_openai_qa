from copy import deepcopy
import os
from time import sleep
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel
import streamlit as st

from model.answers_generation import MarkdownAnswer, OpenAIConfig, QuestionsAnswers, QuestionsAnswersI, QuestionsAnswersMock
from defaults import OPTIMUS_IMAGE
from ingestion.db_manager import VectorStoreFilesDB
from model.files_manager import FileLink, InMemoryFilesManager, SheetFilesDB
from utils.drive_utils import DriveConfig, get_sheet_service
from utils.dotenv_utils import load_config
from model.feedback.feedback import TestLog, SheetLogWriter, YesNoPartially



openai_config: OpenAIConfig = load_config(OpenAIConfig, os.getenv)
drive_config: DriveConfig = load_config(DriveConfig, os.getenv)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str | MarkdownAnswer


TEST_CONVERSATION = [
        ChatMessage(role="assistant", content="Hola, soy Optimus, en qué puedo ayudarte?")
    ]


if "conversation" not in st.session_state:
    st.session_state.conversation = deepcopy(TEST_CONVERSATION)
if 'answer_model' not in st.session_state:
    st.session_state.answer_model = QuestionsAnswers(openai_config)
    # st.session_state.answer_model = QuestionsAnswersMock()
if 'files_manager' not in st.session_state:
    sheet_service = get_sheet_service(drive_config)
    vs_files_db = VectorStoreFilesDB(sheet_service,
                                    "1XAhPXBsAecJUiyI13l6qtiI-iuITA4XjyDI11BLmGDo",
                                    "VectorStore",
                                    openai_config.VECTOR_STORE_ID)
    st.session_state.files_manager = SheetFilesDB(vs_files_db)

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

        answer_model: QuestionsAnswersI = st.session_state.answer_model
        answer = answer_model.answer(message)

        markdown_answer = MarkdownAnswer.from_llm_answer(answer, st.session_state.files_manager)
        conversation.append(ChatMessage(role="assistant", content=markdown_answer))


def main():
    client = OpenAI(api_key=openai_config.OPENAI_API_KEY, organization=openai_config.OPENAI_ORG_ID)
    assistant = client.beta.assistants.retrieve(openai_config.ASSISTANT_ID)

    # st.button("Reset chat", on_click=reset_chat)
    
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

    
    prompt = st.chat_input("Say something", key="message", on_submit=submit_message)

    st.button("Reset chat", on_click=reset_chat)

if __name__ == '__main__':
    main()
