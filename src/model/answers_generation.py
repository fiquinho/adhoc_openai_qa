from concurrent.futures import thread
from time import sleep
from typing import Protocol
from openai import OpenAI
from openai.types.beta.threads import Message
from pydantic import BaseModel

from model.files_manager import FilesManagerI


class OpenAIConfig(BaseModel):
    OPENAI_API_KEY: str
    OPENAI_ORG_ID: str


class FileAnnotation(BaseModel):
    text: str       # The text as it appears in the answer
    file_id: str    # The id of the referenced file


class LLMAnswer(BaseModel):
    answer: str
    references: list[FileAnnotation]
    thread_id: str
    run_id: str


class QuestionsAnswersI(Protocol):
    def answer(self, question: str, vector_store_id: str) -> LLMAnswer: ...


class QuestionsAnswersMock:

    def answer(self, _: str, __: str) -> LLMAnswer:
        sleep(1)
        answer = "This is a mock answer\n\n[[REF 1]]\n\n[[REF 2]]"
        references = [
            FileAnnotation(text="[[REF 1]]", file_id="mock_file_1"),
            FileAnnotation(text="[[REF 2]]", file_id="mock_file_2")
        ]
        return LLMAnswer(
            answer=answer, 
            references=references,
            thread_id="mock_thread_id",
            run_id="mock_run_id")


class QuestionsAnswers:
    def __init__(self, client: OpenAI, assistant_id: str):

        self.client = client
        self.assistant = self.client.beta.assistants.retrieve(assistant_id)

    def answer(self, question: str, vector_store_id: str) -> LLMAnswer:

        thread = self.client.beta.threads.create(
            tool_resources={
                "file_search": {"vector_store_ids": [vector_store_id]}
            }
        )
        
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
            for annotation in content.text.annotations:  # type: ignore
                annotation_obj = FileAnnotation(
                    text=annotation.text, 
                    file_id=annotation.file_citation.file_id)  # type: ignore
                references.append(annotation_obj)

            llm_answer = LLMAnswer(
                answer=content.text.value,  # type: ignore
                references=references,
                thread_id=thread.id,
                run_id=run.id)

            return llm_answer

        else:
            raise Exception(f"Thread run failed with status {run.status}")


class MarkdownAnswer(BaseModel):
    text: str
    references: list[str]
    references_urls: set[str]
    thread_id: str
    run_id: str

    @classmethod
    def from_llm_answer(cls, answer: LLMAnswer, files_manager: FilesManagerI) -> 'MarkdownAnswer':
        answer_text = answer.answer
        references = []
        references_urls = set()
        for i, r in enumerate(answer.references):
            reference_text = f" [ Referencia #{i + 1} ]"
            answer_text = answer_text.replace(r.text, reference_text)

            file_link = files_manager.get_file_link(r.file_id)
            file_name = file_link.name
            file_url = file_link.url
            reference_text = f" {i + 1}. [{file_name}]({file_url})\n\n"

            if file_url in references_urls:
                continue

            references.append(reference_text)
            references_urls.add(file_url)
        return cls(text=answer_text, 
                   references=references, 
                   references_urls=references_urls,
                   thread_id=answer.thread_id,
                   run_id=answer.run_id)
