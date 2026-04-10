import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@telegram-apps/telegram-ui/dist/styles.css'
import './styles/global.css'
import { App } from './App'
import { ensureTelegramSdk, initTelegram } from './lib/telegram'

async function bootstrap() {
  await ensureTelegramSdk()
  initTelegram()

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

void bootstrap()
