from pathlib import Path


PROJECT_PATH = Path(__file__).resolve().parent.parent
CORE_PATH = PROJECT_PATH / 'src'

DEFAULT_ENV_FILE = PROJECT_PATH / ".env"
DRIVE_CREDENTIALS_FILE = PROJECT_PATH / "drive_credentials.json"
DRIVE_TOKEN_FILE = PROJECT_PATH / "drive_token.json"

DEV_ENV_FILE = PROJECT_PATH / "dev.env"
