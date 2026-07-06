"""Exécution des migrations Alembic au démarrage."""

import logging
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.config import settings
from app.database import engine

logger = logging.getLogger(__name__)


def executer_migrations() -> None:
    alembic_ini = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

    insp = inspect(engine)
    if not insp.has_table("alembic_version") and insp.has_table("users"):
        logger.info("Base existante détectée — tampon Alembic 001_baseline.")
        command.stamp(alembic_cfg, "001_baseline")

    command.upgrade(alembic_cfg, "head")
