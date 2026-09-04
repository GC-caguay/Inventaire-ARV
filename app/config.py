from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    db_path: Path = BASE_DIR / "data" / "arv.db"
    default_loan_days: int = 7
    host: str = "127.0.0.1"
    port: int = 8000


settings = Settings()
settings.db_path.parent.mkdir(parents=True, exist_ok=True)
