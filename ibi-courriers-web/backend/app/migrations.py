"""Migrations légères du schéma (sans Alembic)."""

from sqlalchemy import inspect, text

from app.database import engine


def appliquer_migrations_schema() -> None:
    insp = inspect(engine)
    if not insp.has_table("users"):
        return

    colonnes = {c["name"] for c in insp.get_columns("users")}
    with engine.begin() as conn:
        if "must_change_password" not in colonnes:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN must_change_password "
                    "BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )
