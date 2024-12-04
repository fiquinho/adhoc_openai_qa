import json

import streamlit as st

from src.defaults import DEFAULT_ENV_FILE, PROJECT_PATH
from src.model.files_manager import InMemoryFilesManager, FileLink
from src.model.main import OpenAIConfig, QuestionsAnswers
from src.utils.dotenv_utils import config_from_env


def main():
    config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)

    with open(PROJECT_PATH / "file_links.json", "r") as f:
        files_dict = json.load(f)

    file_links_dict = {}
    for key, value in files_dict.items():
        file_links_dict[key] = FileLink(**value)
    files_manager = InMemoryFilesManager(file_links_dict)

    answers_model = QuestionsAnswers(config, files_manager)

    st.text_area("Ask a question", key="question")

    if st.button("Ask"):
        question = st.session_state.question
        answer = answers_model.answer(question)
        st.markdown(answer)


if __name__ == '__main__':
    main()
