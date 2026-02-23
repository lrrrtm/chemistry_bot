const BASE = "/api";

function getToken(): string | null {
  return localStorage.getItem("admin_token");
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers ?? {}),
    },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const json = JSON.parse(text);
      detail = json.detail ?? text;
    } catch {}
    throw new Error(detail || `Ошибка ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Auth
  login: (password: string) =>
    request<{ token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  verify: () => request<{ ok: boolean }>("/auth/verify"),

  recoverPassword: () =>
    request<{ ok: boolean }>("/auth/recover-password", { method: "POST" }),

  // Users
  getUsers: () =>
    request<Array<{ id: number; telegram_id: number; name: string }>>(
      "/admin/users"
    ),

  renameUser: (telegram_id: number, name: string) =>
    request<{ ok: boolean }>(`/admin/users/${telegram_id}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    }),

  deleteUser: (telegram_id: number) =>
    request<{ ok: boolean }>(`/admin/users/${telegram_id}`, {
      method: "DELETE",
    }),

  getUserStats: (telegram_id: number) =>
    request<
      Array<{
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
      }>
    >(`/admin/users/${telegram_id}/stats`),

  // Topics
  getTopics: () =>
    request<
      Record<
        string,
        Array<{
          id: number;
          name: string;
          tags: Array<{ tag: string; count: number }>;
        }>
      >
    >("/admin/topics"),

  // Hand works
  createHandWork: (payload: {
    name: string;
    questions: Record<string, number>;
    mode: string;
    hard_tags?: string[];
    questions_count?: number;
  }) =>
    request<{
      id: number;
      name: string;
      identificator: string;
      link: string | null;
    }>("/admin/hand-works", { method: "POST", body: JSON.stringify(payload) }),

  getHandWorks: () =>
    request<Array<{ id: number; name: string; identificator: string; created_at: string; questions_count: number; link: string | null }>>(
      "/admin/hand-works"
    ),

  deleteHandWork: (id: number) =>
    request<{ ok: boolean }>(`/admin/hand-works/${id}`, { method: "DELETE" }),

  sendTrainingToUser: (data: { telegram_id: number; link: string; name: string }) =>
    request<{ ok: boolean }>("/admin/send-training", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Pool
  getPool: () =>
    request<Array<{ id: number; text: string; tags_list: string[] }>>(
      "/admin/pool"
    ),

  getQuestion: (id: number) =>
    request<{
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
    }>(`/admin/pool/${id}`),

  updateQuestion: (
    id: number,
    data: {
      text: string;
      answer: string;
      level: number;
      full_mark: number;
      tags_list: string[];
      is_rotate: number;
      is_selfcheck: number;
    }
  ) =>
    request<{ ok: boolean }>(`/admin/pool/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteQuestion: (id: number) =>
    request<{ ok: boolean }>(`/admin/pool/${id}`, { method: "DELETE" }),

  addQuestion: (data: {
    text: string;
    answer: string;
    type: string;
    level: number;
    full_mark: number;
    tags_list: string[];
    is_rotate: boolean;
    is_selfcheck: boolean;
  }) => request<{ id: number; ok: boolean }>("/admin/pool", { method: "POST", body: JSON.stringify(data) }),

  uploadQuestionImage: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/admin/pool/${id}/question-image`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    }).then((r) => r.json());
  },

  deleteQuestionImage: (id: number) =>
    request<{ ok: boolean }>(`/admin/pool/${id}/question-image`, {
      method: "DELETE",
    }),

  uploadAnswerImage: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/admin/pool/${id}/answer-image`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    }).then((r) => r.json());
  },

  deleteAnswerImage: (id: number) =>
    request<{ ok: boolean }>(`/admin/pool/${id}/answer-image`, {
      method: "DELETE",
    }),

  // Topics Excel
  exportTopicsExcel: () =>
    fetch(`${BASE}/admin/topics/export`, { headers: authHeaders() }).then((r) => {
      if (!r.ok) throw new Error("Export failed");
      return r.blob();
    }),

  importTopicsExcel: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/admin/topics/import`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    }).then(async (r) => {
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Import failed");
      return data as { ok: boolean; message: string };
    });
  },

  createTopic: (name: string, volume: string) =>
    request<{ id: number; name: string; volume: string; tags: [] }>("/admin/topics", {
      method: "POST",
      body: JSON.stringify({ name, volume }),
    }),

  deleteTopic: (topicId: number) =>
    request<{ ok: boolean }>(`/admin/topics/${topicId}`, { method: "DELETE" }),

  updateTopicTags: (topicId: number, tags_list: string[]) =>
    request<{ ok: boolean }>(`/admin/topics/${topicId}`, {
      method: "PUT",
      body: JSON.stringify({ tags_list }),
    }),

  // Pool Excel import
  getPoolTemplate: () =>
    fetch(`${BASE}/admin/pool/template`, { headers: authHeaders() }).then((r) => {
      if (!r.ok) throw new Error("Download failed");
      return r.blob();
    }),

  importPoolExcel: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/admin/pool/import`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    }).then(async (r) => {
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Import failed");
      return data as { ok: boolean; imported_count: number; message: string };
    });
  },

  // Backup settings
  getBackupSettings: () =>
    request<{ time: string; chat_id: string; yadisk_token: string }>("/admin/backup-settings"),

  saveBackupSettings: (data: { time: string; chat_id: string; yadisk_token: string }) =>
    request<{ ok: boolean }>("/admin/backup-settings", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  runBackupNow: () =>
    request<{ ok: boolean; message: string }>("/admin/backup-now", { method: "POST" }),

  // Yandex Disk backups
  getYadiskBackups: () =>
    request<Array<{ name: string; path: string; size: number; modified: string; created: string }>>(
      "/admin/yadisk-backups"
    ),

  restoreFromYadisk: (path: string) =>
    request<{ ok: boolean; message: string }>("/admin/yadisk-restore", {
      method: "POST",
      body: JSON.stringify({ path }),
    }),

  // Backup restore
  restoreBackup: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/admin/restore`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    }).then(async (r) => {
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Restore failed");
      return data as { ok: boolean; message: string };
    });
  },

  // EGE converting
  getEgeConverting: () =>
    request<Array<{ id: number; input_mark: number; output_mark: number }>>(
      "/admin/ege-converting"
    ),

  updateEgeConverting: (data: Record<string, number>) =>
    request<{ ok: boolean }>("/admin/ege-converting", {
      method: "PUT",
      body: JSON.stringify({ data }),
    }),

  // Student (public)
  getWorkStats: (token: string) =>
    request<{
      general: {
        telegram_id: number;
        user_name: string | null;
        name: string;
        start: string | null;
        end: string | null;
        final_mark: number;
        max_mark: number;
        fully: number;
        semi: number;
        zero: number;
      };
      questions: Array<{
        index: number;
        question_id: number;
        text: string;
        answer: string;
        user_answer: string;
        user_mark: number;
        full_mark: number;
        question_image: boolean;
        answer_image: boolean;
      }>;
    }>(`/student/work-stats?token=${token}`),

  imageUrl: {
    question: (id: number) => `${BASE}/images/question/${id}`,
    answer: (id: number) => `${BASE}/images/answer/${id}`,
    user: (telegram_id: number) => `${BASE}/images/user/${telegram_id}`,
  },
};
