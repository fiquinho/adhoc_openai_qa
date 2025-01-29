import json

import pandas as pd
from tqdm import tqdm
from pydantic import BaseModel

from defaults import DEFAULT_ENV_FILE
from model.answers_generation import MarkdownAnswer, OpenAIConfig, QuestionsAnswers

from ingestion.db_manager import VectorStoreFilesDB
from model.files_manager import SheetFilesDB
from autotest.db_manager import SheetManager
from utils.dotenv_utils import FromFileConfigGenerator, load_config
from utils.drive_utils import DriveConfig, get_document_id, get_sheet_service


class AutotestExample(BaseModel):
    question_id: int
    question: str
    gold_document_id: str
    assistant_id: str
    answer: str
    answer_sources_ids: list[str]


def main():
    file_config_generator = FromFileConfigGenerator(DEFAULT_ENV_FILE)
    drive_config: DriveConfig = load_config(DriveConfig, file_config_generator.get_config)
    sheet_service = get_sheet_service(drive_config)

    openai_config: OpenAIConfig = load_config(OpenAIConfig, file_config_generator.get_config)

    spreadsheet_id = '1Ax7kL_8lvBWSWQlNAtVrHAUNX_9Ep9gn04FNGXJSob0'
    sheet_name = 'Hoja 2'

    sheet_manager = SheetManager(sheet_service, spreadsheet_id, sheet_name)
    questions = sheet_manager.get_questions()

    DB_SPREADSHEET_ID = "1XAhPXBsAecJUiyI13l6qtiI-iuITA4XjyDI11BLmGDo"
    DB_SHEET_NAME = "VectorStore"

    vs_files_db = VectorStoreFilesDB(sheet_service,
                                     DB_SPREADSHEET_ID,
                                     DB_SHEET_NAME,
                                     openai_config.VECTOR_STORE_ID)
    files_manager = SheetFilesDB(vs_files_db)

    vs_files = vs_files_db.get_all()
    vs_files_df = pd.DataFrame([file.model_dump() for file in vs_files])
    
    filtered_questions = []
    for q in questions:
        if q.gold_document_id not in vs_files_df['source_id'].values:
            print(f"Missing source file: {q.gold_document_id}")
        else:
            filtered_questions.append(q)
    
    qa = QuestionsAnswers(openai_config)

    answers: list[AutotestExample] = []
    for q in tqdm(filtered_questions):
        llm_answer = qa.answer(q.question)
        markdown_answer = MarkdownAnswer.from_llm_answer(llm_answer, files_manager)
        autotest_example = AutotestExample(
            question_id=q.id,
            question=q.question,
            gold_document_id=q.gold_document_id,
            assistant_id=openai_config.VECTOR_STORE_ID,
            answer=llm_answer.answer,
            answer_sources_ids=[get_document_id(r) for r in markdown_answer.references_urls]
        )
        answers.append(autotest_example)
    
    with open('answers.json', 'w', encoding="utf8") as f:
        json.dump([a.model_dump() for a in answers], f, indent=4)


if __name__ == '__main__':
    main()
