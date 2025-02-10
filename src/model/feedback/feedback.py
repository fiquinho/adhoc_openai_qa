from concurrent.futures import thread
from typing import Literal

from googleapiclient.discovery import build
from pydantic import BaseModel

from utils.drive_utils import SheetServiceFacade


YesNo = Literal["Yes", "No"]
YesNoPartially = Literal["Yes", "No", "Partially"]


COLUMNS_MAPPING = {
    "ID": "id",
    "Usuario": "user",
    "Versión": "version",
    "Pregunta": "question",
    "Respuesta": "answer",
    "Resolvió tu duda?": "was_solved",
    "Fuente compartida?": "shared_sources",
    "Fuente": "sources",
    "La respuesta fue detallada?": "was_detailed",
    "Sugerencia": "note",
    "Thread ID": "thread_id",
    "Run ID": "run_id"
}


class TestLog(BaseModel):
    user: str
    version: str
    question: str
    answer: str
    was_solved: YesNoPartially
    shared_sources: YesNo
    sources: list[str] | None
    was_detailed: YesNoPartially
    note: str | None
    thread_id: str
    run_id: str


class FeedbackLogsConfig(BaseModel):
    spreadsheet_id: str
    sheet_name: str


class SheetLogWriter:
    def __init__(self, sheet_service: SheetServiceFacade, config: FeedbackLogsConfig):
        self.sheet_service = sheet_service
        self.config = config

    def write(self, test_log: TestLog):
        headers = self.sheet_service.get(self.config.spreadsheet_id, f"{self.config.sheet_name}!1:1")
        last_id = len(self.sheet_service.get(self.config.spreadsheet_id , f"{self.config.sheet_name}!A:A"))

        init_dict = test_log.model_dump()
        init_dict.update({"id": last_id})
        init_dict.update({"sources": ",".join(init_dict["sources"])})

        values_list = [init_dict[COLUMNS_MAPPING[header]] for header in headers[0]]

        self.sheet_service.update(
            self.config.spreadsheet_id, 
            f"{self.config.sheet_name}!A{last_id + 1}", 
            [values_list])

    def get_all(self) -> list[TestLog]:
        result = self.sheet_service.get(
            self.config.spreadsheet_id, 
            f"{self.config.sheet_name}!A2:L")

        return [TestLog(**dict(zip(COLUMNS_MAPPING.values(), r))) for r in result]
        