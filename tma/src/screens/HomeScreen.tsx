import { Banner, Button, Cell, List, Section } from '@telegram-apps/telegram-ui'
import { Brain, FileText } from 'lucide-react'
import { type CachedData } from '../App'
import { HomeScreenSkeleton } from '../components/SkeletonScreens'
import { type NavActions } from '../lib/navigation'
import { haptic } from '../lib/telegram'

interface Props {
  nav: NavActions
  cache: CachedData
}

export function HomeScreen({ nav, cache }: Props) {
  const { activeWork } = cache

  if (activeWork === undefined) {
    return <HomeScreenSkeleton />
  }

  return (
    <List>
      {activeWork && (
        <div style={{ padding: '0 16px 8px' }}>
          <Banner
            type="section"
            // callout="Можно продолжить"
            header="У тебя есть активная тренировка"
            subheader={`Ты можешь продолжить её или начать новую, но тогда прогресс будет потерян`}
          >
            <Button
              size="m"
              stretched
              onClick={() => {
                haptic('selection')
                nav.push({ name: 'question', workId: activeWork.id })
              }}
            >
              Продолжить тренировку
            </Button>
          </Banner>
        </div>
      )}

      <Section header="Новая тренировка">
        <Cell
          before={<FileText size={22} style={{ flexShrink: 0 }} />}
          subtitle="34 вопроса"
          onClick={() => {
            haptic('selection')
            nav.push({ name: 'work-confirm', config: { type: 'ege', workName: 'КИМ ЕГЭ' } })
          }}
        >
          Тренировка в формате ЕГЭ
        </Cell>
        <Cell
          before={<Brain size={22} style={{ flexShrink: 0 }} />}
          subtitle="20 вопросов"
          onClick={() => {
            haptic('selection')
            nav.push({ name: 'topic-select' })
          }}
        >
          Персональная тренировка
        </Cell>
      </Section>
    </List>
  )
}
