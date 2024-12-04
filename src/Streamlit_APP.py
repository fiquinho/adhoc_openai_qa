import streamlit as st

from src.defaults import DEFAULT_ENV_FILE
from src.model.files_manager import create_in_memory_files_manager
from src.model.main import OpenAIConfig, QuestionsAnswers, final_answer_text
from src.utils.dotenv_utils import config_from_env


def main():
    config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)
    files_manager = create_in_memory_files_manager()
    answers_model = QuestionsAnswers(config)

    st.text_area("Ask a question", key="question")

    if st.button("Ask"):
        question = st.session_state.question
        answer = answers_model.answer(question)
        final_text = final_answer_text(answer, files_manager)
        st.markdown(final_text)


if __name__ == '__main__':
    main()
