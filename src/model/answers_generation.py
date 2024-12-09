from openai import OpenAI
from openai.types.beta.threads import Message
from pydantic import BaseModel

from src.defaults import DEFAULT_ENV_FILE
from src.utils.dotenv_utils import config_from_file


class OpenAIConfig(BaseModel):
    OPENAI_API_KEY: str
    OPENAI_ORG_ID: str
    VECTOR_STORE_ID: str
    ASSISTANT_ID: str


class FileAnnotation(BaseModel):
    text: str       # The text as it appears in the answer
    file_id: str    # The id of the referenced file


class LLMAnswer(BaseModel):
    answer: str
    references: list[FileAnnotation]


class QuestionsAnswers:
    def __init__(self, client_config: OpenAIConfig):

        self.client = OpenAI(api_key=client_config.OPENAI_API_KEY, organization=client_config.OPENAI_ORG_ID)
        self.assistant = self.client.beta.assistants.retrieve(client_config.ASSISTANT_ID)

    def answer(self, question: str) -> LLMAnswer:

        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant.id
        )

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )
            m: Message = messages.data[0]
            content = m.content[0]
            references = []
            for i, annotation in enumerate(content.text.annotations):
                annotation_obj = FileAnnotation(text=annotation.text, file_id=annotation.file_citation.file_id)
                references.append(annotation_obj)

            llm_answer = LLMAnswer(answer=content.text.value, references=references)

            return llm_answer

        else:
            raise Exception(f"Thread run failed with status {run.status}")


def main():
    config: OpenAIConfig = config_from_file(DEFAULT_ENV_FILE, OpenAIConfig)
    qa = QuestionsAnswers(config)
    answer = qa.answer("que es la autoimpresión de remitos?")
    print(answer)


if __name__ == '__main__':
    main()
