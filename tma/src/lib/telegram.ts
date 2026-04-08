import { useEffect, useState } from 'react'

interface TgInsets {
  top: number
  bottom: number
  left: number
  right: number
}

interface TgWebApp {
  initData: string
  initDataUnsafe: {
    user?: {
      id: number
      first_name: string
      last_name?: string
      username?: string
      photo_url?: string
    }
    start_param?: string
  }
  colorScheme: 'light' | 'dark'
  platform?: string
  safeAreaInset?: TgInsets
  contentSafeAreaInset?: TgInsets
  viewportHeight?: number
  viewportStableHeight?: number
  isFullscreen?: boolean
  expand: () => void
  requestFullscreen?: () => void
  close?: () => void
  ready: () => void
  disableClosingConfirmation?: () => void
  requestSafeArea?: () => void
  requestContentSafeArea?: () => void
  requestViewport?: () => void
  requestTheme?: () => void
  openTelegramLink?: (url: string) => void
  openLink?: (url: string) => void
  onEvent?: (
    eventType:
      | 'safeAreaChanged'
      | 'contentSafeAreaChanged'
      | 'viewportChanged'
      | 'activated'
      | 'fullscreenChanged'
      | 'fullscreenFailed'
      | 'themeChanged',
    fn: (payload?: { isStateStable?: boolean }) => void,
  ) => void
  offEvent?: (
    eventType:
      | 'safeAreaChanged'
      | 'contentSafeAreaChanged'
      | 'viewportChanged'
      | 'activated'
      | 'fullscreenChanged'
      | 'fullscreenFailed'
      | 'themeChanged',
    fn: (payload?: { isStateStable?: boolean }) => void,
  ) => void
  BackButton: {
    isVisible: boolean
    show: () => void
    hide: () => void
    onClick: (fn: () => void) => void
    offClick: (fn: () => void) => void
  }
  MainButton: {
    text: string
    isVisible: boolean
    isActive: boolean
    setText: (text: string) => void
    show: () => void
    hide: () => void
    enable: () => void
    disable: () => void
    onClick: (fn: () => void) => void
    offClick: (fn: () => void) => void
    showProgress: (leaveActive?: boolean) => void
    hideProgress: () => void
  }
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
    selectionChanged: () => void
  }
}

export const tg = (): TgWebApp | null =>
  (typeof window !== 'undefined' ? (window as Window & { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp : null) ?? null

let backOverride: (() => boolean | void) | null = null

function safeWebAppCall(action: () => void) {
  try {
    action()
  } catch (error) {
    if (import.meta.env.DEV) {
      console.warn('[telegram-webapp] unsupported or failed method call', error)
    }
  }
}

function applyInsets(app: TgWebApp) {
  const safe = app.safeAreaInset ?? { top: 0, bottom: 0, left: 0, right: 0 }
  const content = app.contentSafeAreaInset ?? { top: 0, bottom: 0, left: 0, right: 0 }
  const root = document.documentElement
  const visualViewportHeight = typeof window !== 'undefined' ? window.visualViewport?.height : undefined
  const visualViewportOffsetTop = typeof window !== 'undefined' ? window.visualViewport?.offsetTop ?? 0 : 0
  const viewportHeight = visualViewportHeight ?? app.viewportHeight ?? window.innerHeight
  const viewportStableHeight = app.viewportStableHeight ?? viewportHeight
  const keyboardOffset = Math.max(0, viewportStableHeight - (viewportHeight + visualViewportOffsetTop))

  root.style.setProperty('--tg-safe-area-inset-top', `${safe.top}px`)
  root.style.setProperty('--tg-safe-area-inset-bottom', `${safe.bottom}px`)
  root.style.setProperty('--tg-safe-area-inset-left', `${safe.left}px`)
  root.style.setProperty('--tg-safe-area-inset-right', `${safe.right}px`)
  root.style.setProperty('--tg-content-safe-area-inset-top', `${content.top}px`)
  root.style.setProperty('--tg-content-safe-area-inset-bottom', `${content.bottom}px`)
  root.style.setProperty('--tg-content-safe-area-inset-left', `${content.left}px`)
  root.style.setProperty('--tg-content-safe-area-inset-right', `${content.right}px`)

  root.style.setProperty('--app-viewport-height', `${viewportHeight}px`)
  root.style.setProperty('--app-viewport-stable-height', `${viewportStableHeight}px`)
  root.style.setProperty('--app-keyboard-offset', `${keyboardOffset > 80 ? keyboardOffset : 0}px`)
}

export function initTelegram() {
  const app = tg()
  if (!app) return

  const enterFullscreen = () => {
    safeWebAppCall(() => app.expand())
    if (!app.isFullscreen) {
      if (app.requestFullscreen) {
        safeWebAppCall(() => app.requestFullscreen?.())
      }
    }
  }

  safeWebAppCall(() => app.expand())
  safeWebAppCall(() => app.ready())
  enterFullscreen()
  if (app.disableClosingConfirmation) safeWebAppCall(() => app.disableClosingConfirmation?.())
  if (app.requestSafeArea) safeWebAppCall(() => app.requestSafeArea?.())
  if (app.requestContentSafeArea) safeWebAppCall(() => app.requestContentSafeArea?.())
  if (app.requestViewport) safeWebAppCall(() => app.requestViewport?.())
  if (app.requestTheme) safeWebAppCall(() => app.requestTheme?.())
  requestAnimationFrame(enterFullscreen)

  applyInsets(app)
  const handleViewportResize = () => applyInsets(app)
  app.onEvent?.('safeAreaChanged', () => applyInsets(app))
  app.onEvent?.('contentSafeAreaChanged', () => applyInsets(app))
  app.onEvent?.('activated', () => enterFullscreen())
  app.onEvent?.('viewportChanged', () => applyInsets(app))
  window.visualViewport?.addEventListener('resize', handleViewportResize)
  window.visualViewport?.addEventListener('scroll', handleViewportResize)
}

export function getTgColorScheme(): 'light' | 'dark' {
  return tg()?.colorScheme ?? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
}

export function useTelegramColorScheme() {
  const [appearance, setAppearance] = useState<'light' | 'dark'>(() => getTgColorScheme())

  useEffect(() => {
    const app = tg()
    const updateAppearance = () => setAppearance(getTgColorScheme())

    updateAppearance()
    app?.requestTheme?.()
    app?.onEvent?.('themeChanged', updateAppearance)

    const media = typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)') : null
    media?.addEventListener?.('change', updateAppearance)

    return () => {
      app?.offEvent?.('themeChanged', updateAppearance)
      media?.removeEventListener?.('change', updateAppearance)
    }
  }, [])

  return appearance
}

export function useBackButton(onBack: () => void, active: boolean) {
  useEffect(() => {
    const app = tg()
    if (!app?.BackButton) return

    if (active) {
      app.BackButton.show()
      app.BackButton.onClick(onBack)
      return () => {
        app.BackButton.offClick(onBack)
        app.BackButton.hide()
      }
    }

    app.BackButton.hide()
  }, [active, onBack])
}

export function getTgUser() {
  return tg()?.initDataUnsafe?.user ?? null
}

export function getInitData(): string {
  return tg()?.initData ?? ''
}

export function getStartParam(): string | undefined {
  const telegramStartParam = tg()?.initDataUnsafe?.start_param
  if (telegramStartParam) return telegramStartParam

  if (typeof window === 'undefined') return undefined

  const params = new URLSearchParams(window.location.search)
  return (
    params.get('startapp')
    ?? params.get('start_param')
    ?? params.get('tgWebAppStartParam')
    ?? undefined
  )
}

export function setBackOverride(handler: (() => boolean | void) | null) {
  backOverride = handler
}

export function consumeBackOverride(): boolean {
  if (!backOverride) return false
  backOverride()
  return true
}

export function haptic(type: 'impact' | 'success' | 'error' | 'selection' = 'impact') {
  const hf = tg()?.HapticFeedback
  if (!hf) return
  if (type === 'impact') hf.impactOccurred('medium')
  else if (type === 'success') hf.notificationOccurred('success')
  else if (type === 'error') hf.notificationOccurred('error')
  else hf.selectionChanged()
}

export function openTelegramUrl(url: string) {
  const app = tg()
  if (app?.openTelegramLink && /^(https?:\/\/t\.me\/|tg:\/\/)/i.test(url)) {
    app.openTelegramLink(url)
    return
  }
  if (app?.openLink) {
    app.openLink(url)
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

export function openExternalUrl(url: string) {
  const app = tg()
  if (app?.openLink) {
    app.openLink(url)
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

export function closeMiniApp() {
  tg()?.close?.()
}
