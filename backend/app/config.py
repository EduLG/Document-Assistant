import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    chat_model: str = os.getenv("CHAT_MODEL", "gemini-3.6-flash")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    chroma_dir: str = str(BASE_DIR / os.getenv("CHROMA_DIR", "./chroma_db"))
    upload_dir: str = str(BASE_DIR / os.getenv("UPLOAD_DIR", "./data/uploads"))
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()

if not settings.google_api_key:
    raise RuntimeError("GOOGLE_API_KEY no está configurada. Define backend/.env a partir de .env.example")

os.makedirs(settings.chroma_dir, exist_ok=True)
os.makedirs(settings.upload_dir, exist_ok=True)
