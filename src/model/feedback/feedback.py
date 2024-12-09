from typing import Literal

from googleapiclient.discovery import build
from pydantic import BaseModel


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


class TestLogRegister(TestLog):
    id: int


class SheetLogWriter:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = build("sheets", "v4", credentials=credentials)

    def write(self, test_log: TestLog):
        sheet = self.service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId="1zE8eiNN_C5n7FTLoAufAvAdGbfm5wUwrnFqqqzgskYQ", range="Hoja 1!1:1")
            .execute()
        )
        headers = result.get("values", [])

        # get last id
        result = (
            sheet.values()
            .get(spreadsheetId="1zE8eiNN_C5n7FTLoAufAvAdGbfm5wUwrnFqqqzgskYQ", range="Hoja 1!A:A")
            .execute()
        )
        last_id = len(result.get("values", []))

        init_dict = test_log.model_dump()
        init_dict.update({"id": last_id})
        init_dict.update({"sources": ",".join(init_dict["sources"])})

        values_list = [init_dict[COLUMNS_MAPPING[header]] for header in headers[0]]

        body = {"values": [values_list]}

        result = (
            sheet.values()
            .append(
                spreadsheetId="1zE8eiNN_C5n7FTLoAufAvAdGbfm5wUwrnFqqqzgskYQ",
                range=f"Hoja 1!A{last_id + 1}",
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

