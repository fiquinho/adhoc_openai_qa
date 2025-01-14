
# If modifying these scopes, delete the file token.json.
import os
import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from defaults import DRIVE_CREDENTIALS_FILE, DRIVE_TOKEN_FILE


SCOPES = ["https://www.googleapis.com/auth/drive"]

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists(DRIVE_TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(DRIVE_TOKEN_FILE, SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            DRIVE_CREDENTIALS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(DRIVE_TOKEN_FILE, "w") as token:
        creds_dict = json.loads(creds.to_json())
        json.dump(creds_dict, token, indent=4)
