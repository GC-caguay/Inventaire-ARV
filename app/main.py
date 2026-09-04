from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import dashboard, inventory, loans, members, parties

app = FastAPI(title="Inventaire ARV")

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)

app.include_router(dashboard.router)
app.include_router(inventory.router)
app.include_router(members.router)
app.include_router(parties.router)
app.include_router(loans.router)
