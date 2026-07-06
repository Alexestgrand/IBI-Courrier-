"""Version de session JWT pour révocation."""

import sqlalchemy as sa
from alembic import op

revision = "003_token_version"
down_revision = "002_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
