from openai import OpenAI
from openai.types.beta.threads import Message
from pydantic import BaseModel

from src.defaults import DEFAULT_ENV_FILE
from src.model.files_manager import FilesManagerI, create_in_memory_files_manager
from src.utils.dotenv_utils import config_from_env


class OpenAIConfig(BaseModel):
    OPENAI_API_KEY: str
    OPENAI_ORG_ID: str
    VECTOR_STORE_ID: str
    ASSISTANT_ID: str


class QuestionsAnswers:
    def __init__(self, client_config: OpenAIConfig, files_manager: FilesManagerI):

        self.client = OpenAI(api_key=client_config.OPENAI_API_KEY, organization=client_config.OPENAI_ORG_ID)
        self.assistant = self.client.beta.assistants.retrieve(client_config.ASSISTANT_ID)
        self.files_manager = files_manager

    def answer(self, question: str):

        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
            instructions=""
        )

        if run.status == 'completed':
            final_answer = ""

            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )
            m: Message = messages.data[0]
            for content in m.content:
                answer_object = content.text
                answer_raw_text = answer_object.value
                annotations = answer_object.annotations

                references = []
                for i, annotation in enumerate(annotations):
                    text_reference = f" [ Referencia #{i + 1} ]"
                    file_link = self.files_manager.get_file_link(annotation.file_citation.file_id)
                    file_name = file_link.source.name
                    file_url = file_link.source.url
                    references.append(f"[{file_name}]({file_url})\n\n![Thumbnail]({file_link.source.thumbnail})\n\n")
                    answer_raw_text = answer_raw_text.replace(annotation.text, text_reference)

                final_answer += answer_raw_text + "\n\n"
                final_answer += "Referencias:\n"

                for i, r in enumerate(references):
                    final_answer += f" {i + 1}. {r}\n"

            return final_answer

        else:
            print(run.status)


def main():
    config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)
    files_manager = create_in_memory_files_manager()
    qa = QuestionsAnswers(config, files_manager)
    answer = qa.answer("que es la autoimpresion de remitos?")
    print(answer)

    # client = OpenAI(api_key=config.OPENAI, organization=config.OPENAI_ORG)
    # vector_stores = client.beta.vector_stores.list()


if __name__ == '__main__':
    main()
