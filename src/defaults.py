from pathlib import Path


PROJECT_PATH = Path(__file__).resolve().parent.parent
CORE_PATH = PROJECT_PATH / 'src'

DEFAULT_ENV_FILE = PROJECT_PATH / ".env"
DEFAULT_CONFIG_FILE = CORE_PATH / "configs" / "config.toml"
DRIVE_CREDENTIALS_FILE = PROJECT_PATH / "drive_credentials.json"
DRIVE_TOKEN_FILE = PROJECT_PATH / "drive_token.json"

DEV_ENV_FILE = PROJECT_PATH / "dev.env"
DEV_CONFIG_FILE = CORE_PATH / "configs" / "config.dev.toml"

OPTIMUS_IMAGE = CORE_PATH / "pages" / "optimus.png"
