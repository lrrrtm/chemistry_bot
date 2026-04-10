import type { AdminTopicsTree } from "@/lib/types";

const BASE = "/api";
const NGROK_SKIP_WARNING_HEADER = { "ngrok-skip-browser-warning": "1" } as const;

function getToken(): string | null {
  return localStorage.getItem("admin_token");
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return {
    ...NGROK_SKIP_WARNING_HEADER,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...NGROK_SKIP_WARNING_HEADER,
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
    } catch {
      // Keep original text when the response is not JSON.
    }
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
    request<Array<{ id: number; telegram_id: number | null; name: string; username: string | null; has_credentials: boolean; telegram_linked: boolean }>>(
      "/admin/users"
    ),

  createStudent: (name: string) =>
    request<{
      user: { id: number; telegram_id: number | null; name: string; username: string | null; has_credentials: boolean; telegram_linked: boolean };
      invite_token: string;
      invite_url: string | null;
      invite_expires_at: string;
    }>("/admin/users", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  regenerateStudentInvite: (userId: number) =>
    request<{
      user: { id: number; telegram_id: number | null; name: string; username: string | null; has_credentials: boolean; telegram_linked: boolean };
      invite_token: string;
      invite_url: string | null;
      invite_expires_at: string;
    }>(`/admin/users/${userId}/invite`, {
      method: "POST",
    }),

  issueStudentWebAccessLink: (userId: number) =>
    request<{
      user: { id: number; telegram_id: number | null; name: string; username: string | null; has_credentials: boolean; telegram_linked: boolean };
      invite_token: string;
      invite_url: string | null;
      invite_expires_at: string;
    }>(`/admin/users/${userId}/web-access-link`, {
      method: "POST",
    }),

  renameUser: (userId: number, name: string) =>
    request<{ ok: boolean }>(`/admin/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    }),

  deleteUser: (userId: number) =>
    request<{ ok: boolean }>(`/admin/users/${userId}`, {
      method: "DELETE",
    }),

  getUserStats: (userId: number) =>
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
    >(`/admin/users/${userId}/stats`),

  // Topics
  getTopics: () => request<AdminTopicsTree>("/admin/topics"),

  // Theory documents
  getTheoryDocuments: (query = "") =>
    request<Array<{
      id: number;
      title: string;
      tags_list: string[];
      file_size: number;
      mime_type: string;
      created_at: string | null;
    }>>(`/admin/theory-documents?query=${encodeURIComponent(query)}`),

  createTheoryDocument: (payload: {
    title: string;
    tags_list: string[];
    file: File;
  }) => {
    const form = new FormData();
    form.append("title", payload.title);
    form.append("tags_json", JSON.stringify(payload.tags_list));
    form.append("file", payload.file);
    return fetch(`${BASE}/admin/theory-documents`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    }).then(async (r) => {
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Upload failed");
      return data as {
        ok: boolean;
        document: {
          id: number;
          title: string;
          tags_list: string[];
          file_size: number;
          mime_type: string;
          created_at: string | null;
        };
      };
    });
  },

  updateTheoryDocument: (
    id: number,
    data: { title: string; tags_list: string[] }
  ) =>
    request<{
      ok: boolean;
      document: {
        id: number;
        title: string;
        tags_list: string[];
        file_size: number;
        mime_type: string;
        created_at: string | null;
      };
    }>(`/admin/theory-documents/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  replaceTheoryDocumentFile: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/admin/theory-documents/${id}/file`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    }).then(async (r) => {
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Replace failed");
      return data as {
        ok: boolean;
        document: {
          id: number;
          title: string;
          tags_list: string[];
          file_size: number;
          mime_type: string;
          created_at: string | null;
        };
      };
    });
  },

  deleteTheoryDocument: (id: number) =>
    request<{ ok: boolean }>(`/admin/theory-documents/${id}`, {
      method: "DELETE",
    }),

  theoryDocumentUrl: (id: number) => `${BASE}/theory-documents/${id}/file`,

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
      web_link: string | null;
    }>("/admin/hand-works", { method: "POST", body: JSON.stringify(payload) }),

  getHandWorks: () =>
    request<Array<{ id: number; name: string; identificator: string; created_at: string; questions_count: number; link: string | null; web_link: string | null }>>(
      "/admin/hand-works"
    ),

  downloadHandWorkPdf: (identificator: string) =>
    fetch(`${BASE}/admin/hand-works/${identificator}/pdf`, { headers: authHeaders() }).then(async (r) => {
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || "Download failed");
      }
      return r.blob();
    }),

  deleteHandWork: (id: number) =>
    request<{ ok: boolean }>(`/admin/hand-works/${id}`, { method: "DELETE" }),

  sendTrainingToUser: (data: { telegram_id: number; identificator: string; name: string }) =>
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
