"""Migrations légères du schéma (sans Alembic)."""

from sqlalchemy import inspect, text

from app.database import engine


def _ajouter_colonne_si_absente(
    table: str,
    colonne: str,
    definition_sql: str,
) -> None:
    insp = inspect(engine)
    if not insp.has_table(table):
        return
    colonnes = {c["name"] for c in insp.get_columns(table)}
    if colonne not in colonnes:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {definition_sql}"))


def appliquer_migrations_schema() -> None:
    insp = inspect(engine)
    if not insp.has_table("users"):
        return

    _ajouter_colonne_si_absente(
        "users",
        "must_change_password",
        "must_change_password BOOLEAN NOT NULL DEFAULT FALSE",
    )
    _ajouter_colonne_si_absente(
        "users",
        "chemin_signature",
        "chemin_signature VARCHAR(500)",
    )

    _ajouter_colonne_si_absente(
        "courriers",
        "signe_par_id",
        "signe_par_id INTEGER REFERENCES users(id)",
    )
    _ajouter_colonne_si_absente(
        "courriers",
        "signe_le",
        "signe_le TIMESTAMP WITH TIME ZONE",
    )
