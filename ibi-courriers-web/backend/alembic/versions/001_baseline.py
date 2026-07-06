"""Schéma initial — tables SQLAlchemy."""

from alembic import op

revision = "001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app import models  # noqa: F401
    from app.database import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app import models  # noqa: F401
    from app.database import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
