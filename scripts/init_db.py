from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.database import SessionLocal
from app.models import Category
from scripts.backup_db import backup_db

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_CATEGORIES = [
    "Caméras",
    "Objectifs",
    "Piles",
    "Trépieds",
    "Éclairage",
    "Speaker",
    "Câbles",
    "Cartes mémoire",
    "Autre",
]


def init_db() -> None:
    backup_db()

    alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BASE_DIR / "migrations"))
    command.upgrade(alembic_cfg, "head")

    db = SessionLocal()
    try:
        # Renommage ponctuel : "Audio" -> "Speaker" (préserve les items déjà liés à cette catégorie).
        audio = db.query(Category).filter(Category.name == "Audio").first()
        if audio and not db.query(Category).filter(Category.name == "Speaker").first():
            audio.name = "Speaker"
            db.add(audio)
            db.commit()

        existing = {c.name for c in db.query(Category).all()}
        for name in DEFAULT_CATEGORIES:
            if name not in existing:
                db.add(Category(name=name))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Base de données initialisée.")
