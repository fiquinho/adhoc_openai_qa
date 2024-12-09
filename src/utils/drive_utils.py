from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pydantic import BaseModel


class DriveConfig(BaseModel):
    DRIVE_CLIENT_ID: str
    DRIVE_PROJECT_ID: str
    CLIENT_SECRET: str
    DRIVE_TOKEN: str
    DRIVE_REFRESH_TOKEN: str


SCOPES = ["https://www.googleapis.com/auth/drive"]
DRIVE_TOKEN_TEMPLATE = {
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": SCOPES,
    "universe_domain": "googleapis.com",
    "account": "",
    "expiry": "2024-12-09T13:12:15.397414Z"
}
DRIVE_CREDENTIALS_TEMPLATE = {
    "auth_uri":"https://accounts.google.com/o/oauth2/auth",
    "token_uri":"https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris":["http://localhost"]
}


class CredentialsError(Exception):
    pass


class DriveCredentials:
    def __init__(self, config: DriveConfig):
        self.config = config
        token_dict = DRIVE_TOKEN_TEMPLATE.copy()
        token_dict.update({
            "token": config.DRIVE_TOKEN,
            "refresh_token": config.DRIVE_REFRESH_TOKEN,
            "client_id": config.DRIVE_CLIENT_ID,
            "client_secret": config.CLIENT_SECRET
        })
        self.token_dict = token_dict

    def get_drive_credentials(self) -> Credentials:
        creds = Credentials.from_authorized_user_info(self.token_dict, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise CredentialsError("Invalid DRIVE credentials")

            # Save the credentials for the next run
            self.token_dict = creds.to_json()

        return creds
