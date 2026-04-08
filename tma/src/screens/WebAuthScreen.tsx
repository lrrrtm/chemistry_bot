import { useEffect, useMemo, useState } from 'react'
import { Button, Input } from '@telegram-apps/telegram-ui'

import { api, type InvitePreview, type StudentProfile } from '../api'
import { AnimatedPlaceholder } from '../components/AnimatedPlaceholder'
import duckHeyAnimation from '../assets/duckHeyAnimation.json'
import { haptic } from '../lib/telegram'
import { clearStudentToken, getInviteToken, setStudentToken } from '../lib/studentAuth'

interface Props {
  onAuthenticated: (profile: StudentProfile) => void
}

export function WebAuthScreen({ onAuthenticated }: Props) {
  const inviteToken = getInviteToken()
  const [mode, setMode] = useState<'activate' | 'login'>(inviteToken ? 'activate' : 'login')
  const [inviteInfo, setInviteInfo] = useState<InvitePreview | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!inviteToken) {
      setMode('login')
      return
    }
    setMode('activate')
    api.inspectInvite(inviteToken).then(setInviteInfo).catch((inviteError: Error) => {
      setError(inviteError.message)
      setMode('login')
    })
  }, [inviteToken])

  const canSubmit = useMemo(() => username.trim().length >= 3 && password.trim().length >= 6, [password, username])

  const handleActivate = async () => {
    if (!inviteToken || !canSubmit || loading) return
    setLoading(true)
    setError('')
    try {
      const result = await api.activateInvite(inviteToken, username.trim(), password)
      setStudentToken(result.token)
      haptic('success')
      onAuthenticated(result.profile)
    } catch (requestError) {
      clearStudentToken()
      setError(requestError instanceof Error ? requestError.message : 'Не удалось активировать приглашение')
      haptic('error')
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async () => {
    if (!canSubmit || loading) return
    setLoading(true)
    setError('')
    try {
      const result = await api.loginWithCredentials(username.trim(), password)
      setStudentToken(result.token)
      haptic('success')
      onAuthenticated(result.profile)
    } catch (requestError) {
      clearStudentToken()
      setError(requestError instanceof Error ? requestError.message : 'Не удалось войти')
      haptic('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 12px 16px' }}>
        <AnimatedPlaceholder
          title={mode === 'activate' ? 'Привет!' : 'Вход в профиль'}
          description={
            mode === 'activate'
              ? inviteInfo
                ? `Придумай логин и пароль, чтобы открывать Химбот не только в Telegram`
                : 'Подготовим доступ к твоему профилю'
              : 'Введи логин и пароль от профиля'
          }
          animationData={duckHeyAnimation}
        />

        <div style={{ padding: '0 4px', marginTop: 12, display: 'grid', gap: 12 }}>
          <div className="app-input-shell">
            <Input
              className="app-wide-input"
              placeholder="Логин"
              value={username}
              onChange={(event) => {
                setUsername(event.target.value)
                setError('')
              }}
              autoCapitalize="off"
              autoCorrect="off"
              disabled={loading}
            />
          </div>
          <div className="app-input-shell">
            <Input
              className="app-wide-input"
              placeholder="Пароль"
              type="password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value)
                setError('')
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  void (mode === 'activate' ? handleActivate() : handleLogin())
                }
              }}
              disabled={loading}
            />
          </div>

          {error && (
            <div style={{ color: 'var(--tgui--destructive_text_color, #e8361e)', fontSize: 13, padding: '0 8px' }}>
              {error}
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: '16px', paddingBottom: 'var(--content-safe-offset)' }}>
        <Button
          size="l"
          stretched
          loading={loading}
          disabled={!canSubmit || loading}
          onClick={() => void (mode === 'activate' ? handleActivate() : handleLogin())}
        >
          {mode === 'activate' ? 'Сохранить и войти' : 'Войти'}
        </Button>
      </div>
    </div>
  )
}
