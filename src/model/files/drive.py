DRIVE_MIMETYPES_DICT = {
    "application/vnd.google-apps.document": "docx",
    "application/vnd.google-apps.spreadsheet": "xlsx"
}


class NameCleaner:

    def __init__(self, types_dict: dict[str, str], delete: list[str], replace: str):
        self.types_dict = types_dict
        self.delete = delete
        self.replace = replace

    def clean_name(self, name: str, mime_type: str) -> str:
        for c in self.delete:
            name = name.replace(c, self.replace)

        extension = self.types_dict.get(mime_type, None)
        if extension is not None:
            name = name + '.' + extension

        return name


class DriveNameCleaner(NameCleaner):

    def __init__(self):
        super().__init__(types_dict=DRIVE_MIMETYPES_DICT,
                         delete=['/', ':', '?'],
                         replace='_')
