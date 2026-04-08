import { useState, useEffect } from 'react'
import { AppRoot, Tabbar } from '@telegram-apps/telegram-ui'

// Sync page background with AppRoot theme so there's no white flash outside the component tree
function useAppearance() {
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const [appearance, setAppearance] = useState<'dark' | 'light'>(mq.matches ? 'dark' : 'light')
  useEffect(() => {
    const handler = (e: MediaQueryListEvent) => setAppearance(e.matches ? 'dark' : 'light')
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return appearance
}
import { TopicsScreen } from './screens/TopicsScreen'
import { QuestionScreen } from './screens/QuestionScreen'
import { StatsScreen } from './screens/StatsScreen'

type Tab = 'topics' | 'stats'
type Screen = { name: 'topics' } | { name: 'question'; topicId: number } | { name: 'stats' }

export function App() {
  const appearance = useAppearance()
  const [screen, setScreen] = useState<Screen>({ name: 'topics' })
  const [tab, setTab] = useState<Tab>('topics')

  const handleTabChange = (t: Tab) => {
    setTab(t)
    setScreen({ name: t })
  }

  const showTabbar = screen.name !== 'question'

  return (
    // style pulls the CSS variable that AppRoot defines on itself, covering the full viewport
    <AppRoot
      platform="ios"
      appearance={appearance}
      style={{ minHeight: '100dvh', background: 'var(--tgui--bg_color)' }}
    >
      {/* Extra bottom padding so the fixed Tabbar doesn't overlap content */}
      <div style={{ paddingBottom: showTabbar ? 80 : 0, minHeight: '100dvh' }}>
        {screen.name === 'topics' && (
          <TopicsScreen
            onTopicSelect={(id) => setScreen({ name: 'question', topicId: id })}
          />
        )}
        {screen.name === 'question' && (
          <QuestionScreen
            topicId={screen.topicId}
            onBack={() => {
              setTab('topics')
              setScreen({ name: 'topics' })
            }}
          />
        )}
        {screen.name === 'stats' && <StatsScreen />}
      </div>

      {/* In v2 Tabbar includes its own FixedLayout */}
      {showTabbar && (
        <Tabbar>
          <Tabbar.Item
            text="Темы"
            selected={tab === 'topics'}
            onClick={() => handleTabChange('topics')}
          >
            📚
          </Tabbar.Item>
          <Tabbar.Item
            text="Статистика"
            selected={tab === 'stats'}
            onClick={() => handleTabChange('stats')}
          >
            📊
          </Tabbar.Item>
        </Tabbar>
      )}
    </AppRoot>
  )
}
