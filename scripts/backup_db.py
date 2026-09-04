from __future__ import annotations

import shutil
from datetime import datetime

from app.config import settings

BACKUP_DIR = settings.db_path.parent / "backups"
MAX_BACKUPS = 60


def backup_db() -> None:
    """Copie data/arv.db vers data/backups/ avant toute opération risquée (ex. migration)."""
    if not settings.db_path.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"arv-{stamp}.db"
    shutil.copy2(settings.db_path, dest)

    backups = sorted(BACKUP_DIR.glob("arv-*.db"))
    for old in backups[:-MAX_BACKUPS]:
        old.unlink()


if __name__ == "__main__":
    backup_db()
    print(f"Sauvegarde effectuée dans {BACKUP_DIR}")
