import os

import streamlit as st
from pydantic import BaseModel

from model.feedback.feedback import TestLog, SheetLogWriter, YesNoPartially
from model.files_manager import SheetFilesDB, in_memory_files_manager_from_json, FilesManagerI
from model.answers_generation import MarkdownAnswer, OpenAIConfig, QuestionsAnswers, LLMAnswer
from ingestion.db_manager import VectorStoreFilesDB
from utils.dotenv_utils import load_config
from utils.drive_utils import DriveCredentials, DriveConfig, get_sheet_service
from defaults import PROJECT_PATH


class StreamlitConfig(BaseModel):
    STREAMLIT_PASSWORD: str


streamlit_config: StreamlitConfig = load_config(StreamlitConfig, os.getenv)
openai_config: OpenAIConfig = load_config(OpenAIConfig, os.getenv)
drive_config: DriveConfig = load_config(DriveConfig, os.getenv)


if 'answer' not in st.session_state:
    st.session_state.answer: MarkdownAnswer | None = None  # type: ignore
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if 'answer_model' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.answer_model = QuestionsAnswers(openai_config)
if 'files_manager' not in st.session_state:
    sheet_service = get_sheet_service(drive_config)
    vs_files_db = VectorStoreFilesDB(sheet_service,
                                    "1XAhPXBsAecJUiyI13l6qtiI-iuITA4XjyDI11BLmGDo",
                                    "VectorStore",
                                    openai_config.VECTOR_STORE_ID)
    st.session_state.files_manager = SheetFilesDB(vs_files_db)
if 'drive_credentials' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.drive_credentials = DriveCredentials(drive_config)
if 'streamlit_config' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.streamlit_config = streamlit_config


def generate_answer():

    st.session_state.submitted = False

    question: str = st.session_state.question
    answer_model: QuestionsAnswers = st.session_state.answer_model
    answer = answer_model.answer(question)

    markdown_answer = MarkdownAnswer.from_llm_answer(answer, st.session_state.files_manager)
    st.session_state.answer = markdown_answer


def main():

    password = st.text_input("Password", key="password")
    if password != st.session_state.streamlit_config.STREAMLIT_PASSWORD:
        st.stop()

    user = st.text_input("User", key="user")
    if user == "":
        st.stop()

    st.text_area("Ask a question", key="question", on_change=generate_answer)

    if st.session_state.answer is not None:
        answer = st.session_state.answer

        st.markdown("### Respuesta")
        st.markdown(answer.text)
        st.markdown("### Referencias")
        st.session_state.thumbs_list = []
        for reference in answer.references:
            st.markdown(reference)

        # if st.session_state.submitted:
        #     st.success("Submitted")
        #     st.stop()

        with st.form("form"):
            was_solved: YesNoPartially = st.radio("Resolvió tu duda?", options=YesNoPartially.__args__, key="was_solved")
            was_detailed: YesNoPartially = st.radio("La respuesta fue detallada?", options=YesNoPartially.__args__, key="was_detailed")
            note = st.text_area("Sugerencia", key="note")

            test_log = TestLog(
                user=user,
                question=st.session_state.question,
                answer=answer.text,
                was_solved=was_solved,
                shared_sources="Yes" if len(answer.references) > 0 else "No",
                sources=[r for r in answer.references_urls],
                was_detailed=was_detailed,
                note=note if note != "" else None,
                thread_id=answer.thread_id,
                run_id=answer.run_id
            )

            if st.form_submit_button("Submit"):
                sheet_service = get_sheet_service(drive_config)
                # noinspection PyTypeHints
                st.session_state.log_writer = SheetLogWriter(sheet_service)
                st.session_state.log_writer.write(test_log)
                st.success("Submitted")



if __name__ == '__main__':
    main()
