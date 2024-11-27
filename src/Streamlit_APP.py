import streamlit as st

from src.defaults import DEFAULT_ENV_FILE
from src.main import OpenAIConfig, QuestionsAnswers
from src.utils.dotenv_utils import config_from_env


def main():
    config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)

    answers_model = QuestionsAnswers(config)

    st.text_area("Ask a question", key="question")

    if st.button("Ask"):
        question = st.session_state.question
        answer = answers_model.answer(question)
        st.markdown(answer)


if __name__ == '__main__':
    main()
