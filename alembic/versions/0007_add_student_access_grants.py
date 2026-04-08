"""add student access grants

Revision ID: 0007_add_student_access_grants
Revises: 0006_add_student_web_auth
Create Date: 2026-04-08 18:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_add_student_access_grants"
down_revision = "0006_add_student_web_auth"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "student_access_grants"):
        op.create_table(
            "student_access_grants",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("purpose", sa.String(length=50), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("consumed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("created_by", sa.String(length=50), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("token_hash", name="uq_student_access_grants_token_hash"),
        )

    if not _index_exists(bind, "student_access_grants", "ix_student_access_grants_user_purpose"):
        op.create_index(
            "ix_student_access_grants_user_purpose",
            "student_access_grants",
            ["user_id", "purpose"],
            unique=False,
        )

    if not _index_exists(bind, "student_access_grants", "ix_student_access_grants_expires_at"):
        op.create_index(
            "ix_student_access_grants_expires_at",
            "student_access_grants",
            ["expires_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "student_access_grants") and _index_exists(bind, "student_access_grants", "ix_student_access_grants_expires_at"):
        op.drop_index("ix_student_access_grants_expires_at", table_name="student_access_grants")

    if _table_exists(bind, "student_access_grants") and _index_exists(bind, "student_access_grants", "ix_student_access_grants_user_purpose"):
        op.drop_index("ix_student_access_grants_user_purpose", table_name="student_access_grants")

    if _table_exists(bind, "student_access_grants"):
        op.drop_table("student_access_grants")
