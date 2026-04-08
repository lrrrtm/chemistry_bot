import { useState } from 'react'
import { Button, Input } from '@telegram-apps/telegram-ui'
import { api } from '../api'
import { AnimatedPlaceholder } from '../components/AnimatedPlaceholder'
import duckHeyAnimation from '../assets/duckHeyAnimation.json'
import { haptic } from '../lib/telegram'

interface Props {
  onRegistered: () => void
}

export function OnboardingScreen({ onRegistered }: Props) {
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const isValid = name.trim().length >= 2 && name.trim().length <= 30

  const handleSubmit = async () => {
    if (!isValid || loading) return

    setLoading(true)
    setError('')

    try {
      await api.register(name.trim())
      haptic('success')
      onRegistered()
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Не удалось сохранить имя. Попробуй ещё раз.'

      setError(message)
      haptic('error')
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '0 4px',
        }}
      >
        <AnimatedPlaceholder
          title="Привет!"
          description="Химбот поможет тебе подготовиться к экзамену по химии. Тренируйся, изучай теорию и следи за результатами в одном месте."
          animationData={duckHeyAnimation}
        />

        <div style={{ padding: '0 16px', marginTop: 24 }}>
          <div className="app-input-shell">
            <Input
              placeholder="Введи своё имя"
              value={name}
              className="app-wide-input"
              onChange={event => {
                setName(event.target.value)
                setError('')
              }}
              onKeyDown={event => event.key === 'Enter' && void handleSubmit()}
              status={error ? 'error' : 'default'}
              autoFocus
              maxLength={30}
              disabled={loading}
            />
          </div>
          {error && (
            <div
              style={{
                color: 'var(--tgui--destructive_text_color, #e8361e)',
                fontSize: 13,
                marginTop: 6,
                paddingLeft: 4,
              }}
            >
              {error}
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: '16px 16px', paddingBottom: 'var(--content-safe-offset)' }}>
        <Button
          size="l"
          stretched
          disabled={!isValid || loading}
          loading={loading}
          onClick={() => void handleSubmit()}
        >
          Начать подготовку
        </Button>
      </div>
    </div>
  )
}
