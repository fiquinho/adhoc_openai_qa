from typing import Literal

from googleapiclient.discovery import build
from pydantic import BaseModel

from src.utils.drive_utils import SheetServiceFacade


YesNo = Literal["Yes", "No"]
YesNoPartially = Literal["Yes", "No", "Partially"]


COLUMNS_MAPPING = {
    "ID": "id",
    "Usuario": "user",
    "Pregunta": "question",
    "Respuesta": "answer",
    "Resolvió tu duda?": "was_solved",
    "Fuente compartida?": "shared_sources",
    "Fuente": "sources",
    "La respuesta fue detallada?": "was_detailed",
    "Sugerencia": "note"
}


class TestLog(BaseModel):
    user: str
    question: str
    answer: str
    was_solved: YesNoPartially
    shared_sources: YesNo
    sources: list[str] | None
    was_detailed: YesNoPartially
    note: str | None


class SheetLogWriter:
    def __init__(self, sheet_service: SheetServiceFacade):
        self.sheet_service = sheet_service

    def write(self, test_log: TestLog):
        headers = self.sheet_service.get("1zE8eiNN_C5n7FTLoAufAvAdGbfm5wUwrnFqqqzgskYQ", "Hoja 1!1:1")
        last_id = len(self.sheet_service.get("1zE8eiNN_C5n7FTLoAufAvAdGbfm5wUwrnFqqqzgskYQ", "Hoja 1!A:A"))

        init_dict = test_log.model_dump()
        init_dict.update({"id": last_id})
        init_dict.update({"sources": ",".join(init_dict["sources"])})

        values_list = [init_dict[COLUMNS_MAPPING[header]] for header in headers[0]]

        self.sheet_service.update(
            "1zE8eiNN_C5n7FTLoAufAvAdGbfm5wUwrnFqqqzgskYQ", 
            f"Hoja 1!A{last_id + 1}", 
            [values_list])
