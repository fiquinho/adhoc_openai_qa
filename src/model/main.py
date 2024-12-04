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


class Annotation(BaseModel):
    text: str
    file_id: str


class LLMAnswer(BaseModel):
    answer: str
    references: list[Annotation]


def final_answer_text(answer: LLMAnswer, files_manager: FilesManagerI) -> str:
    final_answer = answer.answer

    reference_list = []
    for i, r in enumerate(answer.references):
        reference_text = f" [ Referencia #{i + 1} ]"
        final_answer = final_answer.replace(r.text, reference_text)
        file_link = files_manager.get_file_link(r.file_id)
        file_name = file_link.source.name
        file_url = file_link.source.url
        file_thumbnail = file_link.source.thumbnail
        reference_list.append(f" {i + 1}. [{file_name}]({file_url})\n\n![Thumbnail]({file_thumbnail})\n\n")

    final_answer += "\n\n#### Referencias\n\n"
    final_answer += "\n\n".join(reference_list)

    return final_answer


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
                annotation_obj = Annotation(text=annotation.text, file_id=annotation.file_citation.file_id)
                references.append(annotation_obj)

            llm_answer = LLMAnswer(answer=content.text.value, references=references)

            return llm_answer

        else:
            raise Exception(f"Thread run failed with status {run.status}")


def main():
    config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)
    files_manager = create_in_memory_files_manager()
    qa = QuestionsAnswers(config)
    answer = qa.answer("que es la autoimpresión de remitos?")
    final_text = final_answer_text(answer, files_manager)
    print(final_text)


if __name__ == '__main__':
    main()
