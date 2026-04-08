"""add student web auth fields

Revision ID: 0006_add_student_web_auth
Revises: 0005_add_theory_documents
Create Date: 2026-04-08 14:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_add_student_web_auth"
down_revision = "0005_add_theory_documents"
branch_labels = None
depends_on = None


def _column_names(bind, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def upgrade() -> None:
    bind = op.get_bind()
    columns = _column_names(bind, "users")

    if "telegram_id" in columns:
        op.alter_column(
            "users",
            "telegram_id",
            existing_type=sa.BigInteger(),
            nullable=True,
        )

    if "username" not in columns:
        op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    if "password_hash" not in columns:
        op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    if "invite_token_hash" not in columns:
        op.add_column("users", sa.Column("invite_token_hash", sa.String(length=64), nullable=True))
    if "invite_expires_at" not in columns:
        op.add_column("users", sa.Column("invite_expires_at", sa.DateTime(), nullable=True))
    if "invite_consumed_at" not in columns:
        op.add_column("users", sa.Column("invite_consumed_at", sa.DateTime(), nullable=True))
    if "telegram_link_token_hash" not in columns:
        op.add_column("users", sa.Column("telegram_link_token_hash", sa.String(length=64), nullable=True))
    if "telegram_link_expires_at" not in columns:
        op.add_column("users", sa.Column("telegram_link_expires_at", sa.DateTime(), nullable=True))

    if not _index_exists(bind, "users", "ix_users_username"):
        op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()

    if _index_exists(bind, "users", "ix_users_username"):
        op.drop_index("ix_users_username", table_name="users")

    columns = _column_names(bind, "users")
    for column_name in (
        "telegram_link_expires_at",
        "telegram_link_token_hash",
        "invite_consumed_at",
        "invite_expires_at",
        "invite_token_hash",
        "password_hash",
        "username",
    ):
        if column_name in columns:
            op.drop_column("users", column_name)

    if "telegram_id" in columns:
        op.alter_column(
            "users",
            "telegram_id",
            existing_type=sa.BigInteger(),
            nullable=False,
        )
