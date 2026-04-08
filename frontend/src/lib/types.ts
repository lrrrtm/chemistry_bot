/* ── Shared types used across multiple pages ─────────────────────────── */

export type User = {
  id: number;
  telegram_id: number | null;
  name: string;
  username: string | null;
  has_credentials: boolean;
  telegram_linked: boolean;
};

export type AdminTopicTag = {
  tag: string;
  count: number;
};

export type AdminTopic = {
  id: number;
  name: string;
  tags: AdminTopicTag[];
};

export type AdminTopicsTree = Record<string, AdminTopic[]>;

export type QuestionFull = {
  id: number;
  text: string;
  answer: string;
  level: number;
  full_mark: number;
  tags_list: string[];
  is_rotate: number;
  is_selfcheck: number;
  question_image: boolean;
  answer_image: boolean;
  type: string;
};

export type WorkStat = {
  work_id: number;
  share_token: string | null;
  name: string;
  type: string;
  start: string | null;
  end: string | null;
  final_mark: number;
  max_mark: number;
  fully: number;
  semi: number;
  zero: number;
  questions_amount: number;
};
