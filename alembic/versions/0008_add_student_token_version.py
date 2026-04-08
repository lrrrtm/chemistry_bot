"""add student token version

Revision ID: 0008_add_student_token_version
Revises: 0007_add_student_access_grants
Create Date: 2026-04-08 22:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_add_student_token_version"
down_revision = "0007_add_student_access_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "student_token_version" not in columns:
        op.add_column(
            "users",
            sa.Column("student_token_version", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("users", "student_token_version", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "student_token_version" in columns:
        op.drop_column("users", "student_token_version")
