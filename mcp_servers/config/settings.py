from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv('.env.local')

# [Tool]
DUCKDUCKGO_BASE_URL = os.getenv('DUCKDUCKGO_BASE_URL')
GOOGLE_SEARCH_URL = os.getenv('GOOGLE_WEB_SEARCH_URL')
GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_WEB_SEARCH_API_KEY')
OPEN_WEATHER_MAP_API_KEY = os.getenv('OPEN_WEATHER_MAP_API_KEY')

# [DB]
MILVUS_HOST=os.getenv('MILVUS_HOST')
MILVUS_PORT=os.getenv
ORACLE_USER = os.getenv('ORACLE_USER')
ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD')
ORACLE_DSN = os.getenv('ORACLE_DSN')

# [CORS]
CORS_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000'
]
