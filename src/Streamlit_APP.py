import streamlit as st
from pydantic import BaseModel

from src.defaults import DEFAULT_ENV_FILE
from src.model.feedback.feedback import TestLog, SheetLogWriter
from src.model.files_manager import create_in_memory_files_manager, FilesManagerI
from src.model.answers_generation import OpenAIConfig, QuestionsAnswers, LLMAnswer
from src.utils.dotenv_utils import config_from_file
from src.utils.drive_utils import load_drive_credentials


class MarkdownAnswer(BaseModel):
    text: str
    references: list[str]
    references_urls: set[str]

    @classmethod
    def from_llm_answer(cls, answer: LLMAnswer, files_manager: FilesManagerI) -> 'MarkdownAnswer':
        answer_text = answer.answer
        references = []
        references_urls = set()
        for i, r in enumerate(answer.references):
            reference_text = f" [ Referencia #{i + 1} ]"
            answer_text = answer_text.replace(r.text, reference_text)

            file_link = files_manager.get_file_link(r.file_id)
            file_name = file_link.source.name
            file_url = file_link.source.url
            reference_text = f" {i + 1}. [{file_name}]({file_url})\n\n"

            if file_url in references_urls:
                continue

            references.append(reference_text)
            references_urls.add(file_url)
        return cls(text=answer_text, references=references, references_urls=references_urls)


config: OpenAIConfig = config_from_file(DEFAULT_ENV_FILE, OpenAIConfig)


if 'answer' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.answer: MarkdownAnswer | None = None
if 'submitted' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.submitted = False

if 'answer_model' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.answer_model = QuestionsAnswers(config)
if 'files_manager' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.files_manager = create_in_memory_files_manager()
if 'log_writer' not in st.session_state:
    creds = load_drive_credentials()
    # noinspection PyTypeHints
    st.session_state.log_writer = SheetLogWriter(creds)


def generate_answer():

    st.session_state.submitted = False

    question = st.session_state.question
    answer = st.session_state.answer_model.answer(question)

    # answer_mock = {
    #     "answer": "La autoimpresión de remitos consiste en registrarse en la AFIP como autoimpresor y "
    #               "poder imprimir los remitos completamente desde el sistema, utilizando papel en blanco, "
    #               "sin ningún contenido preimpreso. Esto incluye la impresión del número de CAI en el remito. "
    #               "Para calificar como autoimpresor, es necesario cumplir ciertos requisitos establecidos "
    #               "por la AFIP y se recomienda consultar con un contador sobre el proceso de registro "
    #               "[4:0 source] [4:1 source].",
    #     "references": [
    #         {
    #             "text": "[4:0 source]",
    #             "file_id": "file-RyS5qTuxRyTBKHGn2hqfox"
    #         },
    #         {
    #             "text": "[4:1 source]",
    #             "file_id": "file-Wn7eSdKZw5UKcvshbSvJBQ"
    #         }
    #     ]
    # }
    # answer = LLMAnswer(**answer_mock)

    markdown_answer = MarkdownAnswer.from_llm_answer(answer, st.session_state.files_manager)
    st.session_state.answer = markdown_answer


def main():

    user = st.text_input("User", key="user")
    if user == "":
        st.stop()

    st.text_area("Ask a question", value="que es la autoimpresion de remitos?",
                 key="question", on_change=generate_answer)

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
            was_solved = st.radio("Resolvió tu duda?", options=["Yes", "Partially", "No"], key="was_solved")
            was_detailed = st.radio("La respuesta fue detallada?", options=["Yes", "Partially", "No"], key="was_detailed")
            note = st.text_area("Sugerencia", key="note")

            test_log = TestLog(
                user=user,
                question=st.session_state.question,
                answer=answer.text,
                was_solved=was_solved,
                shared_sources="Yes" if len(answer.references) > 0 else "No",
                sources=[r for r in answer.references_urls],
                was_detailed=was_detailed,
                note=note if note != "" else None
            )

            if st.form_submit_button("Submit"):
                st.session_state.log_writer.write(test_log)
                st.success("Submitted")


if __name__ == '__main__':
    main()
