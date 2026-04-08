"""add theory documents

Revision ID: 0005_add_theory_documents
Revises: 0004_drop_legacy_json
Create Date: 2026-04-05 23:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_add_theory_documents"
down_revision = "0004_drop_legacy_json"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "theory_documents"):
        op.create_table(
            "theory_documents",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("file_name", sa.String(length=255), nullable=False),
            sa.Column("original_file_name", sa.String(length=255), nullable=True),
            sa.Column("mime_type", sa.String(length=100), nullable=False, server_default="application/pdf"),
            sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("file_name", name="uq_theory_documents_file_name"),
        )

    if not _table_exists(bind, "theory_document_tags"):
        op.create_table(
            "theory_document_tags",
            sa.Column("document_id", sa.BigInteger(), nullable=False),
            sa.Column("tag_id", sa.BigInteger(), nullable=False),
            sa.ForeignKeyConstraint(["document_id"], ["theory_documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("document_id", "tag_id", name="pk_theory_document_tags"),
        )

    if not _index_exists(bind, "theory_documents", "ix_theory_documents_is_active_title"):
        op.create_index(
            "ix_theory_documents_is_active_title",
            "theory_documents",
            ["is_active", "title"],
            unique=False,
        )

    if not _index_exists(bind, "theory_document_tags", "ix_theory_document_tags_tag_id"):
        op.create_index(
            "ix_theory_document_tags_tag_id",
            "theory_document_tags",
            ["tag_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "theory_document_tags") and _index_exists(bind, "theory_document_tags", "ix_theory_document_tags_tag_id"):
        op.drop_index("ix_theory_document_tags_tag_id", table_name="theory_document_tags")

    if _table_exists(bind, "theory_documents") and _index_exists(bind, "theory_documents", "ix_theory_documents_is_active_title"):
        op.drop_index("ix_theory_documents_is_active_title", table_name="theory_documents")

    if _table_exists(bind, "theory_document_tags"):
        op.drop_table("theory_document_tags")

    if _table_exists(bind, "theory_documents"):
        op.drop_table("theory_documents")
