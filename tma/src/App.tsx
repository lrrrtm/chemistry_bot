import { Suspense, lazy, useCallback, useEffect, useState, type CSSProperties } from 'react'
import { AppRoot, Button, Tabbar } from '@telegram-apps/telegram-ui'
import { BookOpen, Home, User } from 'lucide-react'

import { ApiError, api, type ActiveWork, type StudentProfile, type WorkListItem } from './api'
import {
  HomeScreenSkeleton,
  ProfileScreenSkeleton,
  QuestionScreenSkeleton,
  SectionCellsSkeleton,
  TopicSelectScreenSkeleton,
  WorkResultsScreenSkeleton,
} from './components/SkeletonScreens'
import { StatePlaceholder } from './components/StatePlaceholder'
import { clearStudentToken, getStudentToken } from './lib/studentAuth'
import {
  consumeBackOverride,
  getInitData,
  getStartParam,
  haptic,
  useBackButton,
  useTelegramColorScheme,
} from './lib/telegram'
import { type NavActions, type Screen, type TabName, TAB_SCREENS } from './lib/navigation'
import { HomeScreen } from './screens/HomeScreen'
import { HandWorkLaunchModal } from './screens/work/HandWorkLaunchModal'

const OnboardingScreen = lazy(() => import('./screens/OnboardingScreen').then(module => ({ default: module.OnboardingScreen })))
const WebAuthScreen = lazy(() => import('./screens/WebAuthScreen').then(module => ({ default: module.WebAuthScreen })))
const TheoryScreen = lazy(() => import('./screens/TheoryScreen').then(module => ({ default: module.TheoryScreen })))
const ProfileScreen = lazy(() => import('./screens/ProfileScreen').then(module => ({ default: module.ProfileScreen })))
const TopicSelectScreen = lazy(() => import('./screens/work/TopicSelectScreen').then(module => ({ default: module.TopicSelectScreen })))
const WorkConfirmScreen = lazy(() => import('./screens/work/WorkConfirmScreen').then(module => ({ default: module.WorkConfirmScreen })))
const QuestionScreen = lazy(() => import('./screens/work/QuestionScreen').then(module => ({ default: module.QuestionScreen })))
const SkippedScreen = lazy(() => import('./screens/work/SkippedScreen').then(module => ({ default: module.SkippedScreen })))
const WorkCompleteScreen = lazy(() => import('./screens/work/WorkCompleteScreen').then(module => ({ default: module.WorkCompleteScreen })))
const WorkResultsScreen = lazy(() => import('./screens/work/WorkResultsScreen').then(module => ({ default: module.WorkResultsScreen })))

type AppStatus = 'loading' | 'onboarding' | 'web-auth' | 'ready' | 'error'

export interface CachedData {
  activeWork: ActiveWork | null | undefined
  works: WorkListItem[] | undefined
  refreshActive: () => void
  refreshWorks: () => void
}

function renderScreen(screen: Screen, nav: NavActions, cache: CachedData, profile: StudentProfile | null, setProfile: (profile: StudentProfile) => void) {
  switch (screen.name) {
    case 'home':
      return <HomeScreen nav={nav} cache={cache} />
    case 'theory':
      return <TheoryScreen />
    case 'profile':
      return <ProfileScreen nav={nav} cache={cache} profile={profile} onProfileRefresh={setProfile} />
    case 'work-type':
      return <HomeScreen nav={nav} cache={cache} />
    case 'topic-select':
      return <TopicSelectScreen nav={nav} />
    case 'work-confirm':
      return <WorkConfirmScreen nav={nav} config={screen.config} cache={cache} profile={profile} />
    case 'question':
      return <QuestionScreen nav={nav} workId={screen.workId} />
    case 'skipped':
      return <SkippedScreen nav={nav} workId={screen.workId} count={screen.count} />
    case 'work-complete':
      return (
        <WorkCompleteScreen
          nav={nav}
          workId={screen.workId}
          onDone={() => {
            cache.refreshActive()
            cache.refreshWorks()
          }}
        />
      )
    case 'work-results':
      return <WorkResultsScreen nav={nav} workId={screen.workId} />
    default:
      return <HomeScreen nav={nav} cache={cache} />
  }
}

function ScreenFallback({ screen }: { screen: Screen }) {
  switch (screen.name) {
    case 'profile':
      return <ProfileScreenSkeleton />
    case 'topic-select':
      return <TopicSelectScreenSkeleton />
    case 'question':
      return <QuestionScreenSkeleton />
    case 'work-results':
      return <WorkResultsScreenSkeleton />
    case 'home':
      return <HomeScreenSkeleton />
    default:
      return <SectionCellsSkeleton rows={3} titleWidth="56%" subtitleWidth="32%" />
  }
}

export function App() {
  const [status, setStatus] = useState<AppStatus>('loading')
  const [profile, setProfile] = useState<StudentProfile | null>(null)
  const [stack, setStack] = useState<Screen[]>([{ name: 'home' }])
  const [activeTab, setActiveTab] = useState<TabName>('home')
  const [activeWork, setActiveWork] = useState<ActiveWork | null | undefined>(undefined)
  const [works, setWorks] = useState<WorkListItem[] | undefined>(undefined)
  const [launchHandWorkId, setLaunchHandWorkId] = useState<string | null>(null)
  const [bootstrapError, setBootstrapError] = useState('')
  const appearance = useTelegramColorScheme()
  const isTelegramRuntime = Boolean(getInitData())
  const shellClassName = isTelegramRuntime ? 'app-shell' : 'app-shell app-shell--web'
  const wrapperClassName = isTelegramRuntime ? 'app-wrapper' : 'app-wrapper app-wrapper--web'
  const tabbarClassName = isTelegramRuntime ? 'app-tabbar' : 'app-tabbar app-tabbar--web'

  const refreshActive = useCallback(() => {
    api.getActiveWork().then(setActiveWork).catch(() => setActiveWork(null))
  }, [])

  const refreshWorks = useCallback(() => {
    api.getWorks().then(setWorks).catch(() => setWorks([]))
  }, [])

  const cache: CachedData = { activeWork, works, refreshActive, refreshWorks }
  const current = stack[stack.length - 1]
  const inFlow = !TAB_SCREENS.includes(current.name)

  const push = useCallback((screen: Screen) => setStack(previous => [...previous, screen]), [])
  const pop = useCallback(() => {
    if (consumeBackOverride()) return
    setStack(previous => (previous.length > 1 ? previous.slice(0, -1) : previous))
  }, [])
  const replace = useCallback((screen: Screen) => setStack(previous => [...previous.slice(0, -1), screen]), [])
  const goToTab = useCallback((tab: TabName) => {
    haptic('selection')
    setActiveTab(tab)
    setStack([{ name: tab }])
  }, [])

  const openLaunchTarget = useCallback(() => {
    const param = getStartParam()
    if (param?.startsWith('work_')) {
      setLaunchHandWorkId(param.replace('work_', ''))
    }
  }, [])

  const bootstrap = useCallback(async () => {
    const hasTelegram = Boolean(getInitData())
    const hasStudentSession = Boolean(getStudentToken())

    if (!hasTelegram && !hasStudentSession) {
      setBootstrapError('')
      setStatus('web-auth')
      return
    }

    try {
      const nextProfile = await api.getMe()
      setProfile(nextProfile)
      setBootstrapError('')

      if (!nextProfile.registered) {
        setStatus(hasTelegram ? 'onboarding' : 'web-auth')
        return
      }

      setStatus('ready')
      refreshWorks()

      const startHandWorkId = getStartParam()?.startsWith('work_')
        ? getStartParam()?.replace('work_', '')
        : undefined

      const active = await api.getActiveWork().catch(() => null)
      setActiveWork(active)

      if (startHandWorkId && active?.work_type === 'hand_work' && active.hand_work_id === startHandWorkId) {
        push({ name: 'question', workId: active.id })
        return
      }

      openLaunchTarget()
    } catch (error) {
      const isUnauthorized = error instanceof ApiError && error.status === 401
      if (isUnauthorized) {
        clearStudentToken()
        setProfile(null)
        setBootstrapError('')
        setStatus(hasTelegram ? 'onboarding' : 'web-auth')
        return
      }

      setBootstrapError(error instanceof Error ? error.message : 'Не удалось загрузить приложение')
      setStatus('error')
    }
  }, [openLaunchTarget, push, refreshWorks])

  useBackButton(pop, inFlow)

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  const rootStyle: CSSProperties = { height: 'var(--app-viewport-stable-height)', background: 'var(--tgui--bg_color)' }
  const tabbarStyle: CSSProperties = { minHeight: 'var(--tabbar-height)', boxSizing: 'border-box' }

  if (status === 'loading') {
    return (
      <AppRoot appearance={appearance} style={rootStyle}>
        <div className={shellClassName}>
          <div className={wrapperClassName}>
            <div className="screen-scroll">
              <HomeScreenSkeleton />
            </div>
          </div>
        </div>
      </AppRoot>
    )
  }

  if (status === 'onboarding') {
    return (
      <AppRoot appearance={appearance} style={rootStyle}>
        <div className={shellClassName}>
          <div className={wrapperClassName}>
            <Suspense fallback={<HomeScreenSkeleton />}>
              <OnboardingScreen
                onRegistered={() => {
                  void api.getMe().then(nextProfile => {
                    setProfile(nextProfile)
                    setStatus('ready')
                    refreshActive()
                    refreshWorks()
                    openLaunchTarget()
                  })
                }}
              />
            </Suspense>
          </div>
        </div>
      </AppRoot>
    )
  }

  if (status === 'web-auth') {
    return (
      <AppRoot appearance={appearance} style={rootStyle}>
        <div className={shellClassName}>
          <div className={wrapperClassName}>
            <Suspense fallback={<HomeScreenSkeleton />}>
              <WebAuthScreen
                onAuthenticated={nextProfile => {
                  setProfile(nextProfile)
                  setStatus('ready')
                  refreshWorks()
                  void api.getActiveWork().then(active => {
                    setActiveWork(active)
                    const startHandWorkId = getStartParam()?.startsWith('work_')
                      ? getStartParam()?.replace('work_', '')
                      : undefined

                    if (startHandWorkId && active?.work_type === 'hand_work' && active.hand_work_id === startHandWorkId) {
                      push({ name: 'question', workId: active.id })
                      return
                    }

                    openLaunchTarget()
                  }).catch(() => {
                    setActiveWork(null)
                    openLaunchTarget()
                  })
                }}
              />
            </Suspense>
          </div>
        </div>
      </AppRoot>
    )
  }

  if (status === 'error') {
    return (
      <AppRoot appearance={appearance} style={rootStyle}>
        <div className={shellClassName}>
          <div className={wrapperClassName}>
            <div className="screen-scroll" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
              <StatePlaceholder
                title="Не удалось загрузить приложение"
                description={bootstrapError || 'Проверь соединение и попробуй еще раз.'}
                action={(
                  <Button size="l" onClick={() => {
                    setStatus('loading')
                    void bootstrap()
                  }}>
                    Повторить
                  </Button>
                )}
              />
            </div>
          </div>
        </div>
      </AppRoot>
    )
  }

  const nav: NavActions = { push, pop, replace, goToTab }

  return (
    <AppRoot appearance={appearance} style={rootStyle}>
      <div className={shellClassName}>
        <div className={wrapperClassName}>
          <div
            className={!inFlow ? 'screen-scroll' : current.name === 'question' || current.name === 'skipped' ? '' : 'flow-scroll'}
            style={current.name === 'question' || current.name === 'skipped' ? { flex: 1, overflow: 'hidden' } : {}}
          >
            <Suspense fallback={<ScreenFallback screen={current} />}>
              {renderScreen(current, nav, cache, profile, nextProfile => setProfile(nextProfile))}
            </Suspense>
          </div>
        </div>

        {!inFlow && (
          <Tabbar key={`tabbar-${appearance}-${activeTab}`} className={tabbarClassName} style={tabbarStyle}>
            <Tabbar.Item text="Главная" selected={activeTab === 'home'} onClick={() => goToTab('home')}>
              <Home size={24} />
            </Tabbar.Item>
            <Tabbar.Item text="Теория" selected={activeTab === 'theory'} onClick={() => goToTab('theory')}>
              <BookOpen size={24} />
            </Tabbar.Item>
            <Tabbar.Item text="Профиль" selected={activeTab === 'profile'} onClick={() => goToTab('profile')}>
              <User size={24} />
            </Tabbar.Item>
          </Tabbar>
        )}
      </div>

      <HandWorkLaunchModal
        open={Boolean(launchHandWorkId)}
        identificator={launchHandWorkId}
        nav={nav}
        onClose={() => setLaunchHandWorkId(null)}
      />
    </AppRoot>
  )
}
