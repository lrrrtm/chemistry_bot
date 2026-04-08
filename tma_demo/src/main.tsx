import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@telegram-apps/telegram-ui/dist/styles.css'
import { App } from './App'

// Full Telegram WebApp mock for browser testing outside Telegram
if (typeof window !== 'undefined' && !(window as any).Telegram) {
  ;(window as any).Telegram = {
    WebApp: {
      initData: '',
      initDataUnsafe: {},
      version: '6.9',
      platform: 'unknown',
      colorScheme: 'light',
      themeParams: {
        bg_color: '#ffffff',
        text_color: '#000000',
        hint_color: '#999999',
        link_color: '#2481cc',
        button_color: '#2481cc',
        button_text_color: '#ffffff',
        secondary_bg_color: '#f1f1f1',
      },
      isExpanded: true,
      viewportHeight: window.innerHeight,
      viewportStableHeight: window.innerHeight,
      isClosingConfirmationEnabled: false,
      headerColor: '#ffffff',
      backgroundColor: '#ffffff',
      ready: () => {},
      expand: () => {},
      close: () => {},
      // Event system — the library uses these to subscribe to viewport/theme changes
      onEvent: (_eventType: string, _handler: () => void) => {},
      offEvent: (_eventType: string, _handler: () => void) => {},
      sendData: (_data: string) => {},
      openLink: (url: string) => window.open(url, '_blank'),
      showAlert: (message: string, callback?: () => void) => { alert(message); callback?.() },
      showConfirm: (message: string, callback?: (ok: boolean) => void) => {
        callback?.(confirm(message))
      },
      MainButton: {
        text: '',
        color: '#2481cc',
        textColor: '#ffffff',
        isVisible: false,
        isActive: true,
        isProgressVisible: false,
        setText: () => {},
        onClick: () => {},
        offClick: () => {},
        show: () => {},
        hide: () => {},
        enable: () => {},
        disable: () => {},
        showProgress: () => {},
        hideProgress: () => {},
      },
      BackButton: {
        isVisible: false,
        onClick: () => {},
        offClick: () => {},
        show: () => {},
        hide: () => {},
      },
      HapticFeedback: {
        impactOccurred: () => {},
        notificationOccurred: () => {},
        selectionChanged: () => {},
      },
    },
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
