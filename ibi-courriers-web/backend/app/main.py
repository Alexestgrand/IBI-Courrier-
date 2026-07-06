"""Point d'entrée FastAPI — IBI Courriers Web."""

import logging
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.health import verifier_sante
from app.migrations import appliquer_migrations_schema
from app.routers import auth, courriers, search, users
from app.seed import initialiser_donnees

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

app.include_router(auth.router, prefix="/api")
app.include_router(courriers.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(search.router, prefix="/api")


def _executer_alembic() -> None:
    try:
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import inspect

        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

        insp = inspect(engine)
        if not insp.has_table("alembic_version"):
            command.stamp(alembic_cfg, "head")
        else:
            command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        logger.warning("Alembic non appliqué : %s", exc)


@app.on_event("startup")
def on_startup() -> None:
    os.makedirs(settings.upload_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    appliquer_migrations_schema()
    _executer_alembic()
    db = SessionLocal()
    try:
        initialiser_donnees(db)
    finally:
        db.close()


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict:
    return verifier_sante(db)
