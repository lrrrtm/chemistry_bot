import { getInitData } from '../lib/telegram'
import { getStudentToken } from '../lib/studentAuth'

const NGROK_SKIP_WARNING_HEADER = { 'ngrok-skip-browser-warning': '1' } as const

export interface StudentProfile {
  registered: boolean
  auth_mode: 'telegram' | 'web'
  telegram_id?: number | null
  telegram_linked: boolean
  has_web_credentials?: boolean
  name?: string
  username?: string | null
}

export interface InvitePreview {
  name: string
  expires_at: string | null
}

export interface AuthResult {
  token: string
  profile: StudentProfile
}

export interface TelegramLinkStartResult {
  ok: boolean
  linked: boolean
  bot_url: string | null
  expires_at?: string
}

export interface WebAccessStartResult {
  mode: 'setup' | 'login'
  url: string
  expires_at?: string
}

export interface Topic {
  id: number
  name: string
  volume: string
}

export interface HandWorkInfo {
  name: string
  identificator: string
  questions_count: number
}

export interface ActiveWork {
  id: number
  work_type: 'ege' | 'topic' | 'hand_work'
  hand_work_id?: string | null
  topic_id?: number | null
  total: number
  answered: number
}

export interface WorkListItem {
  id: number
  work_type: 'ege' | 'topic' | 'hand_work'
  name: string
  final_mark: number
  max_mark: number
  fully: number
  semi: number
  zero: number
  start_datetime: string
  end_datetime: string
}

export interface TheoryDocument {
  id: number
  title: string
  tags_list: string[]
  file_size: number
  created_at: string | null
}

export interface SendTheoryDocumentResult {
  ok: boolean
  chat_url: string
}

export interface CurrentQuestion {
  work_question_id: number
  position: number
  total: number
  question_id: number
  text: string | null
  question_image: boolean
  is_selfcheck: boolean
  full_mark: number
  answer: string | null
  answer_image: boolean
}

export type AdvanceResult =
  | { type: 'question'; question: CurrentQuestion }
  | { type: 'skipped'; count: number }
  | { type: 'complete' }

export interface WorkResult {
  general: {
    telegram_id: number | null
    user_name: string | null
    name: string
    start: string | null
    end: string | null
    final_mark: number
    max_mark: number
    fully: number
    semi: number
    zero: number
  }
  questions: Array<{
    index: number
    question_id: number
    text: string | null
    answer: string
    user_answer: string
    user_mark: number
    full_mark: number
    question_image: boolean
    answer_image: boolean
  }>
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`/api/tma${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...NGROK_SKIP_WARNING_HEADER,
      'X-Telegram-Init-Data': getInitData(),
      'X-Student-Token': getStudentToken(),
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new ApiError((err as { detail?: string }).detail ?? `HTTP ${res.status}`, res.status)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

async function studentAuthRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`/api/student-auth${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...NGROK_SKIP_WARNING_HEADER,
      'X-Student-Token': getStudentToken(),
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new ApiError((err as { detail?: string }).detail ?? `HTTP ${res.status}`, res.status)
  }
  return res.json()
}

async function downloadWithAuth(path: string, fallbackFileName: string) {
  const res = await fetch(`/api/tma${path}`, {
    headers: {
      ...NGROK_SKIP_WARNING_HEADER,
      'X-Telegram-Init-Data': getInitData(),
      'X-Student-Token': getStudentToken(),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new ApiError((err as { detail?: string }).detail ?? `HTTP ${res.status}`, res.status)
  }

  const blob = await res.blob()
  const header = res.headers.get('Content-Disposition') ?? ''
  const matchedName = header.match(/filename="?([^"]+)"?/)
  const fileName = matchedName?.[1] ?? fallbackFileName
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000)
}

export const api = {
  getMe: () => request<StudentProfile>('/me'),
  register: (name: string) =>
    request<StudentProfile>('/register', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  inspectInvite: (inviteToken: string) => studentAuthRequest<InvitePreview>(`/invite/${inviteToken}`),
  activateInvite: (inviteToken: string, username: string, password: string) =>
    studentAuthRequest<AuthResult>('/activate', {
      method: 'POST',
      body: JSON.stringify({ invite_token: inviteToken, username, password }),
    }),
  loginWithCredentials: (username: string, password: string) =>
    studentAuthRequest<AuthResult>('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  verifyStudentSession: () => studentAuthRequest<StudentProfile>('/me'),
  startTelegramLink: () => studentAuthRequest<TelegramLinkStartResult>('/telegram-link/start', { method: 'POST' }),
  startWebAccess: () => request<WebAccessStartResult>('/profile/web-access/start', { method: 'POST' }),
  revokeWebAccess: () => request<StudentProfile>('/profile/web-access', { method: 'DELETE' }),

  getTopics: () => request<Topic[]>('/topics'),
  getTheoryDocuments: (query = '', options?: RequestInit) =>
    request<TheoryDocument[]>(`/theory-documents?query=${encodeURIComponent(query)}`, options),
  sendTheoryDocument: (documentId: number) =>
    request<SendTheoryDocumentResult>(`/theory-documents/${documentId}/send`, { method: 'POST' }),
  getHandWork: (identificator: string) => request<HandWorkInfo>(`/hand-works/${identificator}`),

  getWorks: () => request<WorkListItem[]>('/works'),
  getActiveWork: () => request<ActiveWork | null>('/works/active'),
  abandonWork: () => request<void>('/works/active', { method: 'DELETE' }),

  createWork: (body: {
    work_type: 'ege' | 'topic' | 'hand_work'
    topic_id?: number
    hand_work_id?: string
    replace_active?: boolean
    pdf_delivery?: 'none' | 'telegram' | 'download'
  }) =>
    request<{ work_id: number }>('/works', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  downloadWorkPdf: (workId: number) => downloadWithAuth(`/works/${workId}/pdf`, `training_${workId}.pdf`),

  getCurrentQuestion: (workId: number) => request<CurrentQuestion>(`/works/${workId}/question`),
  submitAnswer: (workId: number, workQuestionId: number, answer: string) =>
    request<AdvanceResult>(`/works/${workId}/answer`, {
      method: 'POST',
      body: JSON.stringify({ work_question_id: workQuestionId, answer }),
    }),
  submitSelfCheck: (workId: number, workQuestionId: number, mark: number) =>
    request<AdvanceResult>(`/works/${workId}/self-check`, {
      method: 'POST',
      body: JSON.stringify({ work_question_id: workQuestionId, mark }),
    }),
  skipQuestion: (workId: number, workQuestionId: number) =>
    request<AdvanceResult>(`/works/${workId}/skip`, {
      method: 'POST',
      body: JSON.stringify({ work_question_id: workQuestionId }),
    }),
  requeueSkipped: (workId: number) => request<void>(`/works/${workId}/requeue-skipped`, { method: 'POST' }),
  finishWork: (workId: number) => request<AdvanceResult>(`/works/${workId}/finish`, { method: 'POST' }),
  getWorkResults: (workId: number) => request<WorkResult>(`/works/${workId}/results`),

  imageUrl: {
    question: (id: number) => `/api/images/question/${id}`,
    answer: (id: number) => `/api/images/answer/${id}`,
    user: (id: number) => `/api/images/user/${id}`,
  },
  documentUrl: (id: number) => `/api/theory-documents/${id}/file`,
  documentViewUrl: (id: number) => `/api/theory-documents/${id}/view`,
}
