from pathlib import Path


PROJECT_PATH = Path(__file__).resolve().parent.parent
CORE_PATH = PROJECT_PATH / 'src'

DEFAULT_ENV_FILE = PROJECT_PATH / ".env"
FICO_ENV_FILE = PROJECT_PATH / "fico.env"
