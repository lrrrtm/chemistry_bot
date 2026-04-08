# Database Schema

## Core entities

- `users`
  - application users
  - business key: `telegram_id`
  - soft delete: `is_deleted`

- `works`
  - a single training attempt
  - belongs to `users`
  - source is one of:
    - `ege`
    - `topic`
    - `hand_work`
  - `topic_id` and `hand_work_id` are nullable and mutually exclusive by application logic

- `work_questions_list`
  - concrete questions inside a `work`
  - tracks order, status, answer, mark, timing
  - `current_work_id` + unique index enforce at most one `current` question per work

## Content entities

- `pool`
  - master bank of questions
  - no JSON tag storage anymore

- `topics`
  - thematic groupings for topic-based training
  - no JSON tag storage anymore

- `hand_works`
  - teacher-curated trainings
  - no JSON question list storage anymore

## Normalized relation tables

- `tags`
  - canonical tag dictionary
  - key field: `slug`

- `pool_tags`
  - many-to-many between `pool` and `tags`

- `topic_tags`
  - many-to-many between `topics` and `tags`

- `hand_work_questions`
  - ordered question list for `hand_works`
  - uniqueness on `(hand_work_id, position)`

## Source of truth

- question tags: `tags` + `pool_tags`
- topic tags: `tags` + `topic_tags`
- hand work composition: `hand_work_questions`
- active current question per work: `work_questions_list.current_work_id`

## Notes

- Legacy JSON columns `pool.tags_list`, `topics.tags_list`, and `hand_works.questions_list` were removed in revision `0004_drop_legacy_json`.
- The runtime may still expose `tags_list` and `questions_list` as Python attributes for compatibility, but they are hydrated from normalized tables, not stored as JSON in MySQL.
