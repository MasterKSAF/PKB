#
#  Load environment variables from .env only
#
import os
from pathlib import Path

from dotenv import load_dotenv

DOTENV_PATH = Path(__file__).parent / '.env'
if not DOTENV_PATH.exists():
    raise FileNotFoundError(f"Required environment file not found: {DOTENV_PATH}")

load_dotenv(dotenv_path=DOTENV_PATH, override=True)

required_vars = [
    'DB_DATABASE',
    'DB_USERNAME',
    'DB_PASSWORD',
    'DB_HOST',
    'DB_PORT',
]

missing = [name for name in required_vars if os.getenv(name) is None]
if missing:
    raise EnvironmentError(f"Missing required environment variables from .env: {', '.join(missing)}")
