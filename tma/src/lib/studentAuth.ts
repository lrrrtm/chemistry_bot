const STUDENT_TOKEN_KEY = 'student_auth_token'

export function getStudentToken() {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem(STUDENT_TOKEN_KEY) ?? ''
}

export function setStudentToken(token: string) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STUDENT_TOKEN_KEY, token)
}

export function clearStudentToken() {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(STUDENT_TOKEN_KEY)
}

export function getInviteToken() {
  if (typeof window === 'undefined') return undefined
  const params = new URLSearchParams(window.location.search)
  return params.get('invite') ?? undefined
}
