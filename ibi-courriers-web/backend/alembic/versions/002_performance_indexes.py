"""Index de performance sur courriers, notifications et audit."""

from alembic import op

revision = "002_performance_indexes"
down_revision = "001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_courriers_statut", "courriers", ["statut"], unique=False, if_not_exists=True
    )
    op.create_index(
        "ix_courriers_type", "courriers", ["type"], unique=False, if_not_exists=True
    )
    op.create_index(
        "ix_courriers_entite_id", "courriers", ["entite_id"], unique=False, if_not_exists=True
    )
    op.create_index(
        "ix_courriers_service_destinataire",
        "courriers",
        ["service_destinataire"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_courriers_service_emetteur",
        "courriers",
        ["service_emetteur"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_courriers_created_at",
        "courriers",
        ["created_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_notifications_user_lu",
        "notifications",
        ["user_id", "lu"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_statuts_log_courrier_id",
        "statuts_log",
        ["courrier_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_audit_log_date", "audit_log", ["date"], unique=False, if_not_exists=True
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_date", table_name="audit_log", if_exists=True)
    op.drop_index("ix_statuts_log_courrier_id", table_name="statuts_log", if_exists=True)
    op.drop_index("ix_notifications_user_lu", table_name="notifications", if_exists=True)
    op.drop_index("ix_courriers_created_at", table_name="courriers", if_exists=True)
    op.drop_index("ix_courriers_service_emetteur", table_name="courriers", if_exists=True)
    op.drop_index(
        "ix_courriers_service_destinataire", table_name="courriers", if_exists=True
    )
    op.drop_index("ix_courriers_entite_id", table_name="courriers", if_exists=True)
    op.drop_index("ix_courriers_type", table_name="courriers", if_exists=True)
    op.drop_index("ix_courriers_statut", table_name="courriers", if_exists=True)
