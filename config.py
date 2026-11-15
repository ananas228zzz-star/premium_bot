import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@ваш_username")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")
GATE_LINK = os.getenv("GATE_LINK", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

DB_PATH = BASE_DIR / "data" / "bot.db"
IMAGES_DIR = BASE_DIR / "images"
WEBAPP_DIR = BASE_DIR / "webapp"