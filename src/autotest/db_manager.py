from pydantic import BaseModel
import pandas as pd

from utils.drive_utils import SheetServiceFacade, get_document_id


ATTRIBUTES_MAPPING = {
    "id": "ID",
    "question": "Pregunta",
    "gold_document_id": "Docu/Heldesk Solution [LINK]"
}


class Question(BaseModel):
    id: int
    question: str
    gold_document_id: str

    @classmethod
    def from_sheet_row(cls, row: dict, mapping: dict[str, str]) -> "Question":
        init_dict = {key: row[value] for key, value in mapping.items()}
        init_dict["gold_document_id"] = get_document_id(init_dict["gold_document_id"])

        return cls(**init_dict)      

def pad_row(row: list, columns: int) -> list:
    return row + [None] * (columns - len(row))


class SheetManager:
    def __init__(self, service: SheetServiceFacade, spreadsheet_id: str, sheet_name: str):
        self.service = service
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

    def get_headers(self) -> list[str]:
        # Get all cells in the first row
        headers = self.service.get(
            spreadsheet_id=self.spreadsheet_id,
            range_=f"{self.sheet_name}!1:1")
        return headers[0]

    def values_as_pd(self) -> pd.DataFrame:
        # Get all values in the sheet
        headers = self.get_headers()
        columns = len(headers)
        range = f"{self.sheet_name}!A2:{chr(65 + columns - 1)}"
        values = self.service.get(
            spreadsheet_id=self.spreadsheet_id,
            range_=range)
        padded_values = [pad_row(row, columns) for row in values]
        return pd.DataFrame(padded_values, columns=headers)
    
    def get_questions(self) -> list[Question]:
        df = self.values_as_pd()
        questions = []
        for row in df.to_dict(orient="records"):
            if row["Docu/Heldesk Solution [LINK]"] is None:
                print(f"Error: Missing gold document id in row {row}")
                continue

            try:
                question = Question.from_sheet_row(row, ATTRIBUTES_MAPPING)
                questions.append(question)
            except ValueError as e:
                print(f"Error: {e}")
                continue

        return questions