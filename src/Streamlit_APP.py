import streamlit as st
from pydantic import BaseModel

from src.defaults import DEFAULT_ENV_FILE
from src.model.files_manager import create_in_memory_files_manager, FilesManagerI
from src.model.answers_generation import OpenAIConfig, QuestionsAnswers, LLMAnswer
from src.utils.dotenv_utils import config_from_env


class MarkdownAnswer(BaseModel):
    text: str
    references: list[str]

    @classmethod
    def from_llm_answer(cls, answer: LLMAnswer, files_manager: FilesManagerI) -> 'MarkdownAnswer':
        answer_text = answer.answer
        references = []
        for i, r in enumerate(answer.references):
            reference_text = f" [ Referencia #{i + 1} ]"
            answer_text = answer_text.replace(r.text, reference_text)

            file_link = files_manager.get_file_link(r.file_id)
            file_name = file_link.source.name
            file_url = file_link.source.url
            file_thumbnail = file_link.source.thumbnail
            reference_text = f" {i + 1}. [{file_name}]({file_url})\n\n![Thumbnail]({file_thumbnail})\n\n"
            references.append(reference_text)
        return cls(text=answer_text, references=references)


config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)


if 'answer' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.answer: MarkdownAnswer | None = None
if 'answer_thumbs' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.answer_thumbs: int | None = None
if 'reference_thumbs' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.reference_thumbs: list[int] | None = None
if 'answer_model' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.answer_model = QuestionsAnswers(config)
if 'files_manager' not in st.session_state:
    # noinspection PyTypeHints
    st.session_state.files_manager = create_in_memory_files_manager()


def reset_state():
    st.session_state.answer = None
    st.session_state.answer_thumbs = None
    st.session_state.reference_thumbs = None


def final_answer_text(markdown_answer: MarkdownAnswer) -> str:
    final_answer = markdown_answer.text
    final_answer += "\n\n#### Referencias\n\n"
    final_answer += "\n\n".join(markdown_answer.references)

    return final_answer


def generate_answer():
    reset_state()
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

    st.text_area("Ask a question", value="que es la autoimpresion de remitos?",
                 key="question", on_change=generate_answer)

    if st.session_state.answer is not None:
        answer = st.session_state.answer

        st.markdown("### Respuesta")
        st.markdown(answer.text)

        answer_thumbs = st.feedback("thumbs", key="answer_thumbs_key")
        st.session_state.answer_thumbs = answer_thumbs
        if st.session_state.answer_thumbs is not None:
            if st.session_state.answer_thumbs == 1:
                st.success("Good answer")
            if st.session_state.answer_thumbs == 0:
                st.error("Bad answer")

        st.markdown("### Referencias")
        st.session_state.thumbs_list = []
        for i, reference in enumerate(answer.references):
            st.markdown(f"Referencia #{i + 1}")
            st.markdown(reference)
            reference_thumbs = st.feedback("thumbs", key=f"reference_{i}_thumbs")
            st.session_state.thumbs_list.append(reference_thumbs)
            if reference_thumbs is not None:
                if reference_thumbs == 1:
                    st.success("Good reference")
                if reference_thumbs == 0:
                    st.error("Bad reference")

        if st.button("submit"):
            print(st.session_state.answer_thumbs, st.session_state.thumbs_list)
            reset_state()


if __name__ == '__main__':
    main()
