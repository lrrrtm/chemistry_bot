"""drop legacy json columns

Revision ID: 0004_drop_legacy_json
Revises: 0003_one_current_workq
Create Date: 2026-04-05 17:10:00
"""
from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa


revision = "0004_drop_legacy_json"
down_revision = "0003_one_current_workq"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    columns = sa.inspect(bind).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def _parse_json_list(raw_value) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, tuple)):
        values = list(raw_value)
    elif isinstance(raw_value, str):
        try:
            decoded = json.loads(raw_value)
        except json.JSONDecodeError:
            return []
        values = decoded if isinstance(decoded, list) else []
    else:
        return []

    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip().lower().replace("\u0451", "\u0435")
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _parse_json_int_list(raw_value) -> list[int]:
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, tuple)):
        values = list(raw_value)
    elif isinstance(raw_value, str):
        try:
            decoded = json.loads(raw_value)
        except json.JSONDecodeError:
            return []
        values = decoded if isinstance(decoded, list) else []
    else:
        return []

    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            continue
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _get_or_create_tag_id(conn, slug: str) -> int:
    existing = conn.execute(
        sa.text("SELECT id FROM tags WHERE slug = :slug"),
        {"slug": slug},
    ).scalar()
    if existing is not None:
        return int(existing)

    conn.execute(
        sa.text("INSERT INTO tags (slug, label, kind) VALUES (:slug, :label, NULL)"),
        {"slug": slug, "label": slug},
    )
    created = conn.execute(
        sa.text("SELECT id FROM tags WHERE slug = :slug"),
        {"slug": slug},
    ).scalar()
    return int(created)


def _backfill_pool_tags(conn) -> None:
    rows = conn.execute(sa.text("SELECT id, tags_list FROM pool")).fetchall()
    for pool_id, raw_tags in rows:
        for slug in _parse_json_list(raw_tags):
            tag_id = _get_or_create_tag_id(conn, slug)
            conn.execute(
                sa.text(
                    """
                    INSERT IGNORE INTO pool_tags (pool_id, tag_id)
                    VALUES (:pool_id, :tag_id)
                    """
                ),
                {"pool_id": pool_id, "tag_id": tag_id},
            )


def _backfill_topic_tags(conn) -> None:
    rows = conn.execute(sa.text("SELECT id, tags_list FROM topics")).fetchall()
    for topic_id, raw_tags in rows:
        for slug in _parse_json_list(raw_tags):
            tag_id = _get_or_create_tag_id(conn, slug)
            conn.execute(
                sa.text(
                    """
                    INSERT IGNORE INTO topic_tags (topic_id, tag_id)
                    VALUES (:topic_id, :tag_id)
                    """
                ),
                {"topic_id": topic_id, "tag_id": tag_id},
            )


def _backfill_hand_work_questions(conn) -> None:
    existing_pool_ids = {
        int(pool_id)
        for (pool_id,) in conn.execute(sa.text("SELECT id FROM pool")).fetchall()
    }
    rows = conn.execute(sa.text("SELECT id, questions_list FROM hand_works")).fetchall()
    for hand_work_id, raw_question_ids in rows:
        for position, question_id in enumerate(_parse_json_int_list(raw_question_ids), start=1):
            if question_id not in existing_pool_ids:
                continue
            conn.execute(
                sa.text(
                    """
                    INSERT IGNORE INTO hand_work_questions (hand_work_id, question_id, position)
                    VALUES (:hand_work_id, :question_id, :position)
                    """
                ),
                {
                    "hand_work_id": hand_work_id,
                    "question_id": question_id,
                    "position": position,
                },
            )


def upgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "pool") and _column_exists(bind, "pool", "tags_list"):
        _backfill_pool_tags(bind)
        op.drop_column("pool", "tags_list")

    if _table_exists(bind, "topics") and _column_exists(bind, "topics", "tags_list"):
        _backfill_topic_tags(bind)
        op.drop_column("topics", "tags_list")

    if _table_exists(bind, "hand_works") and _column_exists(bind, "hand_works", "questions_list"):
        _backfill_hand_work_questions(bind)
        op.drop_column("hand_works", "questions_list")


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "pool") and not _column_exists(bind, "pool", "tags_list"):
        op.add_column("pool", sa.Column("tags_list", sa.JSON(), nullable=False, server_default="[]"))

    if _table_exists(bind, "topics") and not _column_exists(bind, "topics", "tags_list"):
        op.add_column("topics", sa.Column("tags_list", sa.JSON(), nullable=False, server_default="[]"))

    if _table_exists(bind, "hand_works") and not _column_exists(bind, "hand_works", "questions_list"):
        op.add_column("hand_works", sa.Column("questions_list", sa.JSON(), nullable=False, server_default="[]"))
