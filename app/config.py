import os
from dotenv import load_dotenv
load_dotenv()
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tikinsight.db")
COLLECTOR = os.getenv("COLLECTOR", "official").strip().lower()
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()
