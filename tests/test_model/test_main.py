from src.defaults import DEFAULT_ENV_FILE
from src.model.answers_generation import OpenAIConfig, QuestionsAnswers
from src.utils.dotenv_utils import config_from_env


def test_questions_answers():
    config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)

    answers_model = QuestionsAnswers(config)

    pass