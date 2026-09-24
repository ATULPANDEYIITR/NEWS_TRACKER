from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "NEWS TRACKER")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./news_tracker.db",
)

DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

SOURCES_FILE = DATA_DIR / "sources.yaml"

MAX_ARTICLES_PER_SOURCE = int(
    os.getenv("MAX_ARTICLES_PER_SOURCE", "50")
)

EVENT_CLUSTER_LIMIT = int(
    os.getenv("EVENT_CLUSTER_LIMIT", "500")
)
