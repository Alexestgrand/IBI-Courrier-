"""Point d'entrée FastAPI — IBI Courriers Web."""

import logging
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, get_db
from app.health import verifier_sante_publique
from app.migrate import executer_migrations
from app.routers import admin, auth, courriers, notifications, ocr, rapports, search, users
from app.seed import initialiser_donnees
from app.startup_checks import valider_configuration

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IBI Courriers API",
    version="2.1.0",
    description="API de gestion des courriers — Groupe IBI",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(courriers.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(rapports.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(search.router, prefix="/api")


def _executer_migrations_au_demarrage() -> None:
    try:
        executer_migrations()
    except Exception as exc:
        logger.error("Échec des migrations Alembic : %s", exc)
        if settings.environment.lower() in ("production", "prod"):
            raise


@app.on_event("startup")
def on_startup() -> None:
    valider_configuration()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.backup_dir, exist_ok=True)
    os.makedirs(settings.migration_dir, exist_ok=True)
    _executer_migrations_au_demarrage()
    db = SessionLocal()
    try:
        initialiser_donnees(db)
    finally:
        db.close()


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> JSONResponse:
    payload, code = verifier_sante_publique(db)
    return JSONResponse(content=payload, status_code=code)
