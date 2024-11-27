from openai import OpenAI
from openai.pagination import SyncCursorPage
from openai.types.beta import Assistant
from openai.types.beta.threads import Message
from openai.types.beta.vector_stores import VectorStoreFile
from pydantic import BaseModel

from src.defaults import DEFAULT_ENV_FILE
from src.utils.dotenv_utils import config_from_env


class OpenAIConfig(BaseModel):
    OPENAI: str
    OPENAI_ORG: str
    VECTOR_STORE_ID: str
    ASSISTANT_ID: str


config: OpenAIConfig = config_from_env(DEFAULT_ENV_FILE, OpenAIConfig)

# stream = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[{"role": "user", "content": "Say this is a test"}],
#     stream=True,
# )
# for chunk in stream:
#     if chunk.choices[0].delta.content is not None:
#         print(chunk.choices[0].delta.content, end="")


files_references = {
    "Articulo_ Auto impresión.docx": "https://docs.google.com/document/d/1cA0g9nCht5TBP-6mMPJnRoj1AyXW3k4wQD6CIKCNwxI/edit?usp=sharing",
    "Articulo: (v16) Libro de Iva Ventas y Libro de Iva Compras": "https://docs.google.com/document/d/1-Wg7R07aj9nmEeYskRg1C8o9F-KDCQ60qAepFzMF6EI/edit?usp=sharing",
    "Articulo: ¿Cómo verificar la conexión de los WebServices y Puntos de Venta?": "https://docs.google.com/document/d/1fb81vdElPpqZl-5mxkBMaOpEuRrhcgLPnuQ6Iao0TWk/edit?usp=sharing"
}


class QuestionsAnswers:
    def __init__(self, client_config: OpenAIConfig):

        self.client = OpenAI(api_key=client_config.OPENAI, organization=client_config.OPENAI_ORG)
        self.assistant = self.client.beta.assistants.retrieve(client_config.ASSISTANT_ID)
        self.vector_store_files = self.client.beta.vector_stores.files.list(
            vector_store_id=client_config.VECTOR_STORE_ID
        )

    def answer(self, question: str):

        thread = self.client.beta.threads.create()
        message = self.client.beta.threads.messages.create(
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
                    file_name = self.client.files.retrieve(annotation.file_citation.file_id).filename
                    file_link = files_references.get(file_name, None)
                    references.append(f"[{file_name}]({file_link})")
                    answer_raw_text = answer_raw_text.replace(annotation.text, text_reference)

                final_answer += answer_raw_text + "\n\n"
                final_answer += "Referencias:\n"

                for i, r in enumerate(references):
                    final_answer += f" {i + 1}. {r}\n"

            return final_answer

        else:
            print(run.status)


def main():
    qa = QuestionsAnswers(config)
    answer = qa.answer("que es la autoimpresion de remitos?")
    print(answer)


if __name__ == '__main__':
    main()
